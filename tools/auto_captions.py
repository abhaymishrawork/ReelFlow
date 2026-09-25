"""Edit Captions Only orders with no AI chat involved.

  python tools/auto_captions.py              edit the oldest new Captions Only order
  python tools/auto_captions.py <order_id>   edit one specific order
  python tools/auto_captions.py --all        keep going until no new Captions Only orders are left
  add --deliver                              also deliver (upload + email the customer) when QC passes

Steps per order: claim + download (reelflow prepare) -> transcribe to English words -> cut pauses ->
caption with engine/captionfx in the order's style -> QC -> 540p preview -> email the owner.
Without --deliver the order stays "editing" and the owner delivers after watching the preview:
  python reelflow.py deliver <order_id> projects/<order_id>/renders/<order_id>.mp4
Windows Task Scheduler runs this every hour (see tools/auto_captions.cmd and README).
"""
import json, os, subprocess, sys, time, traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import reelflow as rf  # noqa: E402  (loads config, queue and storage)
from core import notify  # noqa: E402

ENGINE = os.path.join(ROOT, "engine", "captionfx", "captionfx.py")
STYLE_DIR = os.path.join(ROOT, "engine", "captionfx", "styles")
LOCK = os.path.join(ROOT, "projects", ".auto_captions.lock")
PAUSE = 0.45            # gaps longer than this are cut
PAD_IN, PAD_OUT = 0.12, 0.18
# Words the engine's scorer likes (long) but that make a weak big caption. Never promote these.
WEAK = set("""because going already doing definitely actually basically really something anything everything
nothing someone anyone everyone recently finally probably maybe also still just very much many then there
here where when what which while about after before again always never ever even only other another thing
things people okay yeah right think thought know knew said says saying tell told telling want wanted make
making made take taking took come coming came give gave getting started start through those these their
they them would could should will shall might must being been have having""".split())


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def run(cmd):
    log("$", " ".join(str(c) for c in cmd))
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")   # Hindi text crashes a cp1252 console
    subprocess.run([str(c) for c in cmd], check=True, env=env)


def words_of(path):
    w = json.load(open(path, encoding="utf-8"))
    return w, (w.get("words", w) if isinstance(w, dict) else w)


def cut_pauses(proj, raw, words_path):
    """Cut every pause longer than PAUSE, write cut.mp4 and words_cut.json with shifted timings."""
    w, W = words_of(words_path)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw],
                               capture_output=True, text=True).stdout.strip())
    segs, cur = [], None
    for x in W:
        if cur and x["s"] - cur[1] > PAUSE:
            segs.append(cur)
            cur = None
        cur = [x["s"], x["e"]] if not cur else [cur[0], x["e"]]
    segs.append(cur)
    merged = []
    for a, b in ([max(0, a - PAD_IN), min(dur, b + PAD_OUT)] for a, b in segs):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    offs, t = [], 0.0
    for a, b in merged:
        offs.append((a, b, t - a))
        t += b - a
    for x in W:
        for a, b, o in offs:
            if a <= x["s"] <= b:
                x["s"], x["e"] = round(x["s"] + o, 3), round(min(x["e"], b) + o, 3)
                break
    for x in W:
        if x["w"].strip(" ,.!?\"'").lower() in WEAK:
            x["hero"] = False
    json.dump(w, open(os.path.join(proj, "words_cut.json"), "w", encoding="utf-8"), indent=1)
    f = "".join("[0:v]trim=%.3f:%.3f,setpts=PTS-STARTPTS[v%d];[0:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,"
                "afade=t=in:d=0.02,afade=t=out:st=%.3f:d=0.03[a%d];" % (a, b, i, a, b, b - a - 0.03, i)
                for i, (a, b, _) in enumerate(offs))
    f += "".join("[v%d][a%d]" % (i, i) for i in range(len(offs))) + "concat=n=%d:v=1:a=1[v][a]" % len(offs)
    open(os.path.join(proj, "cut.txt"), "w").write(f)
    run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-/filter_complex", os.path.join(proj, "cut.txt"),
         "-map", "[v]", "-map", "[a]", "-r", "30", "-c:v", "libx264", "-crf", "14", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", os.path.join(proj, "cut.mp4")])
    return dur, t


def order_style(proj, style_id):
    """The style file with contrast='shadow': keep the style's colours on bright walls, add a heavier shadow."""
    st = json.load(open(os.path.join(STYLE_DIR, style_id + ".json"), encoding="utf-8"))
    specs = list(st.get("roles", {}).values()) + ([st["hero"]["spec"]] if st.get("hero", {}).get("spec") else [])
    for sp in specs:
        sp["contrast"] = "shadow"
        sp["shadow"] = max(sp.get("shadow", 0), 0.55)
    p = os.path.join(proj, "work", "style.json")
    json.dump(st, open(p, "w", encoding="utf-8"), indent=1)
    return p


def probe(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                        "-of", "json", path], capture_output=True, text=True)
    return json.loads(p.stdout or "{}")


def process(oid, deliver=False):
    o = rf.Q.get(oid) or sys.exit("no order " + oid)
    if o.get("tier") != "captions":
        sys.exit("%s is a Full Edit order - that needs the premium-motion-graphics-editor skill" % oid)
    style_id = rf.STYLES.get(o["style"], {}).get("engine_style", o["style"])
    if not os.path.exists(os.path.join(STYLE_DIR, style_id + ".json")):
        raise RuntimeError("no caption engine style '%s'" % style_id)
    log("order", oid, "style", style_id)
    for attempt in range(3):             # big uploads sometimes drop mid-download
        try:
            rf.prepare(oid)
            break
        except Exception:  # noqa: BLE001
            if attempt == 2:
                raise
            log("download failed, retrying")
            time.sleep(10)
    proj = os.path.join(ROOT, "projects", oid)
    raw = next(os.path.join(proj, f) for f in os.listdir(proj) if f.startswith("raw."))
    work = os.path.join(proj, "work")
    lang = "hi" if o["brief"].get("language") == "hi" else "en"   # Hinglish is captioned in English
    out = os.path.join(proj, "renders", oid + ".mp4")

    # 1. transcribe the raw video (words.json with per-word timings)
    run([sys.executable, ENGINE, raw, "-s", style_id, "-o", out, "--plan-only", "--model", "medium",
         "--language", lang, "--workdir", os.path.join(proj, "scan")])
    _, W = words_of(os.path.join(proj, "scan", "words.json"))
    if len(W) < 5:
        raise RuntimeError("only %d words transcribed - no clear speech?" % len(W))

    # 2. cut pauses, 3. caption the cut
    before, after = cut_pauses(proj, raw, os.path.join(proj, "scan", "words.json"))
    log("cut %.1fs -> %.1fs" % (before, after))
    run([sys.executable, ENGINE, os.path.join(proj, "cut.mp4"), "-s", order_style(proj, style_id), "-o", out,
         "--words", os.path.join(proj, "words_cut.json"), "--workdir", work, "--crf", "16"])

    # 4. QC: video + audio, full length, vertical 1080 wide
    info = probe(out)
    kinds = {s.get("codec_type") for s in info.get("streams", [])}
    dur = float(info.get("format", {}).get("duration", 0))
    if not {"video", "audio"} <= kinds or abs(dur - after) > 1.5:
        raise RuntimeError("QC failed: streams %s, %.1fs (expected %.1fs)" % (sorted(kinds), dur, after))

    # 5. small preview for the phone
    prev = os.path.join(work, "preview_540.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", out, "-vf", "scale=540:-2", "-c:v", "libx264", "-b:v", "1300k",
         "-maxrate", "1500k", "-bufsize", "3000k", "-c:a", "aac", "-b:a", "96k", prev])
    rf.Q.set_status(oid, "editing", "auto-captioned, waiting for owner review", project=proj)

    if deliver:
        rf.deliver(oid, out)
        return
    notify.owner("Captions ready to review - " + oid,
                 "Style: %s\nLength: %.0fs (pauses cut from %.0fs)\nPreview: %s\nFull file: %s\n\n"
                 "Happy with it? Deliver:\npython reelflow.py deliver %s projects/%s/renders/%s.mp4"
                 % (style_id, after, before, prev, out, oid, oid, oid), rf.CFG)
    log("ready for review:", out)


def next_captions_order():
    new = [o for o in rf.Q.list("new") if o.get("tier") == "captions"]
    return sorted(new, key=lambda o: o["created"])[0]["id"] if new else None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    deliver, keep_going = "--deliver" in sys.argv, "--all" in sys.argv
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    if os.path.exists(LOCK) and time.time() - os.path.getmtime(LOCK) < 6 * 3600:
        log("another run is still going (lock file) - exit")
        return
    open(LOCK, "w").write(str(os.getpid()))
    try:
        while True:
            oid = args[0] if args else next_captions_order()
            if not oid:
                log("no new Captions Only orders")
                return
            try:
                process(oid, deliver)
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                notify.owner("Auto captions FAILED - " + oid,
                             "%s\nThe order is left as 'editing'. Open Claude and say: process ReelFlow order %s"
                             % (e, oid), rf.CFG)
            if args or not keep_going:
                return
    finally:
        os.remove(LOCK)


if __name__ == "__main__":
    main()
