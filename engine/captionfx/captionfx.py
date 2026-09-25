#!/usr/bin/env python3
"""
captionfx - burn reference-matched animated captions into a talking-head video.

    python captionfx.py INPUT.mp4 --style aura [-o OUT.mp4] [--words words.json]

Pipeline
  1. probe       ffprobe: size, fps, audio
  2. words       faster-whisper word timestamps (or a --words JSON you edited)
  3. plan        group words into phrases, pick hero / accent words, lay out text
  4. matte       u2net_human_seg person matte (only for styles with text behind the subject)
  5. render      per frame: punch-in zoom -> behind layers -> subject -> front layers
  6. encode      libx264 + original audio

Every run writes <workdir>/words.json and <workdir>/plan.json. Edit words.json
(fix spelling or timings, or set "hero": true/false, "accent": true, "br": true
on a word) and re-run with --words to control the result exactly.
"""
import argparse
import copy
import json
import math
import os
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
STYLE_DIR = os.path.join(HERE, "styles")
FONT_DIRS = [
    os.path.join(HERE, "fonts"),
    r"C:\Windows\Fonts",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
    "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
    "/usr/share/fonts",
    os.path.expanduser("~/.fonts"),
]
MATTE_MODEL_CANDIDATES = [
    os.environ.get("CAPTIONFX_MATTE_MODEL", ""),
    os.path.join(HERE, "models", "u2net_human_seg.onnx"),
    os.path.expanduser("~/.cache/hyperframes/background-removal/models/u2net_human_seg.onnx"),
    os.path.expanduser("~/.u2net/u2net_human_seg.onnx"),
]

STOP = set("""a an the and or but so if of to in on at by for from with into onto as is are was were be been being
am do does did have has had it its it's this that these those there here i you he she we they me him her us them my
your his our their mine yours not no yes just very really then than too also can could will would should shall may
might must up out over about what when where who why how all any some more most such only own same s t don't i'm
you're we're they're that's let's get got""".split())

DEFAULTS = {
    "grouping": {"max_words": 3, "max_chars": 22, "break_gap": 0.45, "break_comma": True},
    "timing": {"lead": 0.03, "hold": 0.5, "min_show": 0.35},
    "support": {
        "anchor": [0.5, 0.75], "valign": "center", "align": "center", "max_width": 0.86,
        "layout": "flow", "max_per_line": 3, "word_gap": 0.28, "line_gap": 0.004,
        "preview_opacity": 0.0, "entry": {"type": "fade", "dur": 0.16}, "exit": {"type": "cut", "dur": 0.1},
        "accent_rule": "none", "stagger": [], "behind": False,
    },
    "roles": {
        "base": {"font": ["Poppins-SemiBold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], "size": 0.028,
                 "color": "#FFFFFF", "shadow": 0.35},
    },
    "hero": None,
    "fx": {},
}
HERO_DEFAULTS = {"pick": "score", "min_score": 4, "min_gap": 1.0, "hold": 2.0, "behind": False,
                 "anchor": [0.5, 0.15], "valign": "center", "max_width": 0.9, "repeat": 1,
                 "entry": {"type": "fade", "dur": 0.2}}


# --------------------------------------------------------------------------- utils
def deep_merge(a, b):
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def hex_rgba(c, alpha=1.0):
    c = c.lstrip("#")
    a = int(c[6:8], 16) / 255 if len(c) == 8 else 1.0
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (int(255 * a * alpha),)


def ease_out(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def ease_out_back(u):
    u = min(1.0, max(0.0, u))
    return 1 + 2.4 * (u - 1) ** 3 + 1.4 * (u - 1) ** 2


def core(w):
    return re.sub(r"[^\w$%']", "", w).lower()


def is_num(w):
    return bool(re.search(r"\d", w))


def score(w):
    c = core(w)
    if not c or c in STOP:
        return 0
    return len(c) + (6 if is_num(w) else 0)


def apply_case(t, case):
    if case == "upper":
        return t.upper()
    if case == "lower":
        return t.lower()
    if case == "title":
        return t[:1].upper() + t[1:]
    return t


def strip_punct(t):
    return re.sub(r"^[^\w$]+|[^\w%]+$", "", t) or t


# --------------------------------------------------------------------------- fonts
_font_index = None
_font_cache = {}


def font_index():
    global _font_index
    if _font_index is None:
        _font_index = {}
        for d in FONT_DIRS:
            if not d or not os.path.isdir(d):
                continue
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith((".ttf", ".otf", ".ttc")):
                        _font_index.setdefault(f.lower(), os.path.join(root, f))
    return _font_index


def resolve_font(names):
    """First available font of a stack. "File.ttf@Bold Italic" selects a variable-font instance."""
    if isinstance(names, str):
        names = [names]
    idx = font_index()
    for n in names:
        base, _, var = n.partition("@")
        p = base if os.path.isfile(base) else idx.get(base.lower())
        if p:
            return p, var or None
    raise SystemExit(f"[captionfx] none of these fonts found: {names}. Drop one into {os.path.join(HERE, 'fonts')}")


def load_font(names, size):
    path, var = resolve_font(names)
    key = (path, var, size)
    if key not in _font_cache:
        f = ImageFont.truetype(path, size)
        if var:
            f.set_variation_by_name(var)
        _font_cache[key] = f
    return _font_cache[key]


# --------------------------------------------------------------------------- text sprites
class Sprite:
    """RGBA text image plus metadata: ink bbox, baseline y, text origin x, per-char x offsets."""
    __slots__ = ("img", "ink", "base", "ox", "cx", "size")


_sprite_cache = {}


def gradient(w, h, colors, angle=90):
    """Linear gradient. angle 90 = top->bottom, 0 = left->right, 45 = diagonal."""
    a = math.radians(angle)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    proj = xx * math.cos(a) + yy * math.sin(a)
    proj = (proj - proj.min()) / max(1e-6, proj.max() - proj.min())
    cols = np.array([hex_rgba(c) for c in colors], np.float32)
    stops = np.linspace(0, 1, len(cols))
    out = np.zeros((h, w, 4), np.float32)
    for ch in range(4):
        out[..., ch] = np.interp(proj, stops, cols[:, ch])
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def texture(alpha, kind, seed):
    rng = np.random.default_rng(seed)
    a = np.asarray(alpha, np.float32)
    h, w = a.shape

    def noise(sx, sy, resample):
        small = (rng.random((max(1, h // sy), max(1, w // sx))) * 255).astype(np.uint8)
        return np.asarray(Image.fromarray(small).resize((w, h), resample), np.float32) / 255

    if kind == "chalk":
        grain = rng.random((h, w)).astype(np.float32)
        streak = noise(14, 3, Image.BILINEAR)
        a = a * np.clip(0.25 + 0.55 * grain + 0.45 * streak, 0, 1)
    elif kind == "distress":
        blobs = noise(9, 9, Image.BICUBIC)
        a = a * (blobs > 0.3) * (rng.random((h, w)) > 0.02)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")


def render_text(text, spec, H, scale=1.0, color_override=None):
    key = (text, json.dumps(spec, sort_keys=True), H, round(scale, 4), color_override)
    if key in _sprite_cache:
        return _sprite_cache[key]
    size = max(6, int(round(spec["size"] * H * scale)))
    font = load_font(spec["font"], size)
    t = apply_case(text, spec.get("case"))
    track = spec.get("tracking", 0.0) * size
    stroke = max(1, int(round(spec["stroke"] * size))) if spec.get("stroke") else 0
    glow = spec.get("glow", 0) or 0
    pill = spec.get("pill")
    pad = int(size * 0.6) + stroke + int(size * glow) + (int(size * 0.8) if pill else 0)
    asc, desc = font.getmetrics()
    cx = [font.getlength(t[:i]) + i * track for i in range(len(t) + 1)]
    W, Hh = int(cx[-1]) + 2 + 2 * pad, asc + desc + 2 * pad
    ox, base = pad, pad + asc

    def mask(stroke_w):
        m = Image.new("L", (W, Hh), 0)
        d = ImageDraw.Draw(m)
        if track == 0:
            d.text((ox, base), t, font=font, fill=255, anchor="ls", stroke_width=stroke_w, stroke_fill=255)
        else:
            for i, ch in enumerate(t):
                d.text((ox + cx[i], base), ch, font=font, fill=255, anchor="ls",
                       stroke_width=stroke_w, stroke_fill=255)
        return m

    outer = mask(stroke)
    fill_m = mask(0)
    if spec.get("texture"):
        fill_m = texture(fill_m, spec["texture"], sum(map(ord, text)))
    ink = outer.getbbox() or (0, 0, 1, 1)
    img = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))

    def layer(m, colors, angle=90, alpha=1.0):
        lay = gradient(W, Hh, colors, angle) if len(colors) > 1 else Image.new("RGBA", (W, Hh), hex_rgba(colors[0]))
        lay.putalpha(m.point(lambda v: int(v * alpha)))
        return lay

    if pill:
        px, py = pill.get("pad", [0.35, 0.16])
        rect = (ink[0] - px * size, ink[1] - py * size, ink[2] + px * size, ink[3] + py * size)
        pm = Image.new("L", (W, Hh), 0)
        ImageDraw.Draw(pm).rounded_rectangle(rect, radius=pill.get("radius", 0.3) * size, fill=255)
        if pill.get("glow"):
            img = Image.alpha_composite(img, layer(pm.filter(ImageFilter.GaussianBlur(size * 0.3)), [pill["glow"]]))
        cols = pill.get("gradient") or [pill.get("color", "#000000")]
        img = Image.alpha_composite(img, layer(pm, cols, pill.get("angle", 0), pill.get("opacity", 1.0)))
    if spec.get("shadow"):
        sm = outer.filter(ImageFilter.GaussianBlur(max(1, size * 0.07)))
        sm = sm.transform(sm.size, Image.AFFINE, (1, 0, 0, 0, 1, -max(1, size * 0.035)))
        img = Image.alpha_composite(img, layer(sm, ["#000000"], alpha=spec["shadow"]))
    if glow:
        gm = outer.filter(ImageFilter.GaussianBlur(size * glow * 0.45))
        img = Image.alpha_composite(img, layer(gm, [spec.get("glow_color", spec.get("color", "#FFFFFF"))], alpha=1.3))

    colors = [color_override] if color_override else (spec.get("gradient") or [spec.get("color", "#FFFFFF")])
    if spec.get("outline_only"):
        ring = np.clip(np.asarray(outer, np.int16) - np.asarray(fill_m, np.int16), 0, 255).astype(np.uint8)
        img = Image.alpha_composite(img, layer(Image.fromarray(ring, "L"), colors, spec.get("angle", 90)))
    else:
        if stroke:
            img = Image.alpha_composite(img, layer(outer, [spec.get("stroke_color", "#000000")]))
        img = Image.alpha_composite(img, layer(fill_m, colors, spec.get("angle", 90), spec.get("opacity", 1.0)))

    s = Sprite()
    s.img, s.ink, s.base, s.ox, s.cx, s.size = img, ink, base, ox, cx, size
    _sprite_cache[key] = s
    return s


# --------------------------------------------------------------------------- probe / words
def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    n, d = v["r_frame_rate"].split("/")
    return {"w": int(v["width"]), "h": int(v["height"]), "fps": float(n) / float(d),
            "dur": float(j["format"]["duration"]),
            "audio": any(s["codec_type"] == "audio" for s in j["streams"])}


def transcribe(path, model="small", language=None):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, compute_type="int8")
    segs, _ = m.transcribe(path, word_timestamps=True, vad_filter=True, language=language)
    words = []
    for s in segs:
        for w in s.words:
            t = w.word
            if words and t and not t.startswith(" ") and w.start - words[-1]["e"] < 0.35:
                words[-1]["w"] += t.strip()          # glue "$600" + ",000."
                words[-1]["e"] = round(w.end, 3)
                continue
            if t.strip():
                words.append({"w": t.strip(), "s": round(w.start, 3), "e": round(w.end, 3)})
    return words


# --------------------------------------------------------------------------- planning
def group_words(words, g):
    phrases, cur = [], []
    for w in words:
        if cur:
            prev = cur[-1]
            chars = sum(len(x["w"]) + 1 for x in cur) + len(w["w"])
            if (w.get("br") or len(cur) >= g["max_words"] or w["s"] - prev["e"] > g["break_gap"]
                    or re.search(r"[.!?]$", prev["w"]) or chars > g["max_chars"]
                    or (g.get("break_comma") and prev["w"].endswith((",", ";", ":")))):
                phrases.append(cur)
                cur = []
        cur.append(w)
    if cur:
        phrases.append(cur)
    return phrases


def pick(ph, how):
    cands = [w for w in ph if w.get("hero") is not False]
    if not cands:
        return None
    if how == "first":
        return cands[0]
    if how == "last":
        c = [w for w in cands if score(w["w"])] or cands
        return c[-1]
    if how == "sentence_end":
        return cands[-1] if re.search(r"[.!?]$", cands[-1]["w"]) else None
    return max(cands, key=lambda w: (score(w["w"]), -w["s"]))


def plan(words, st):
    manual = any(w.get("hero") is True for w in words)   # hero:false only excludes a word
    phrases = group_words(words, st["grouping"])
    hero = st.get("hero")
    ih = st.get("inline_hero") if "ihero" in st["roles"] else None
    last_hero, last_ih = -99.0, -99.0
    for ph in phrases:
        for w in ph:
            w["role"] = "base"
        if hero:
            if manual:
                cand = next((w for w in ph if w.get("hero")), None)
            else:
                cand = pick(ph, hero["pick"])
                if cand and hero["pick"] != "first" and score(cand["w"]) < hero["min_score"]:
                    cand = None
                if cand and cand["s"] - last_hero < hero["min_gap"]:
                    cand = None
            if cand:
                cand["role"] = "hero"
                last_hero = cand["s"]
        if ih is not None:
            rest = [w for w in ph if w["role"] == "base"]
            c = None
            if manual:
                c = next((w for w in rest if w.get("hero")), None)
            elif rest:
                c = pick(rest, ih.get("pick", "score"))
                if c and ih.get("pick", "score") == "score" and score(c["w"]) < ih.get("min_score", 4):
                    c = None
                if c and c["s"] - last_ih < ih.get("min_gap", 0):
                    c = None
            if c:
                c["role"] = "ihero"
                last_ih = c["s"]
        rule = st["support"]["accent_rule"]
        rest = [w for w in ph if w["role"] == "base"]
        if any(w.get("accent") for w in ph):
            for w in rest:
                if w.get("accent"):
                    w["role"] = "accent"
        elif rule == "alternate":
            for i, w in enumerate(rest):
                if i % 2 == 1:
                    w["role"] = "accent"
        elif rule == "content" and rest:
            b = max(rest, key=lambda w: score(w["w"]))
            if score(b["w"]) >= 4:
                b["role"] = "accent"
        elif rule == "last" and rest:
            rest[-1]["role"] = "accent"
        if "minor" in st["roles"]:
            for w in ph:
                if w["role"] == "base" and core(w["w"]) in STOP:
                    w["role"] = "minor"
    return phrases


# --------------------------------------------------------------------------- layout
def role_spec(st, role, w=None):
    if role == "hero":
        spec = dict(st["hero"]["spec"])
        if w is not None and is_num(w["w"]) and st["hero"].get("number_spec"):
            spec.update(st["hero"]["number_spec"])
        return spec
    return st["roles"].get(role) or st["roles"]["base"]


def layout_phrase(ph, st, W, H, idx):
    sup = st["support"]
    words = [w for w in ph if w["role"] != "hero"]
    if not words:
        return None
    lines, mode = [], sup["layout"]
    if mode == "lines":
        roles = sup["line_roles"]
        for i, chunk in enumerate(np.array_split(np.arange(len(words)), min(len(words), len(roles)))):
            ln = [words[j] for j in chunk]
            for w in ln:
                if w["role"] == "base":
                    w["role"] = roles[i]
            lines.append(ln)
    elif mode == "stack":
        lines = [[w] for w in words]
    else:
        cur = []
        for w in words:
            if w["role"] == "ihero" and sup.get("hero_own_line", True):
                if cur:
                    lines.append(cur)
                lines.append([w])
                cur = []
                continue
            if len(cur) >= sup["max_per_line"]:
                lines.append(cur)
                cur = []
            cur.append(w)
        if cur:
            lines.append(cur)
        # two lines reads best; merge the shortest neighbouring pair until it fits
        while len(lines) > sup.get("max_lines", 2):
            k = min(range(len(lines) - 1), key=lambda i: len(lines[i]) + len(lines[i + 1]))
            lines[k:k + 2] = [lines[k] + lines[k + 1]]

    has_ih = any(w["role"] == "ihero" for w in words)
    scale = sup.get("ihero_phrase_scale", 1.0) if has_ih else 1.0
    rows = []

    def width(its):
        return sum(s.ink[2] - s.ink[0] for *_, s in its) + sum(
            its[i][1]["size"] * H * its[i][3] * sup["word_gap"] for i in range(len(its) - 1))

    for ln in lines:
        items = []
        for w in ln:
            spec = role_spec(st, w["role"], w)
            txt = strip_punct(w["w"]) if spec.get("strip_punct", sup.get("strip_punct")) else w["w"]
            items.append([w, spec, txt, scale, render_text(txt, spec, H, scale)])
        items = [tuple(i) for i in items]
        lw = sum(it[4].ink[2] - it[4].ink[0] for it in items) + sum(
            items[i][1]["size"] * H * scale * sup["word_gap"] for i in range(len(items) - 1))
        if lw > sup["max_width"] * W:
            k = sup["max_width"] * W / lw
            items = [(w, sp, tx, scale * k, render_text(tx, sp, H, scale * k)) for w, sp, tx, _, _ in items]
            lw *= k
        top = min(it[4].ink[1] - it[4].base for it in items)
        bot = max(it[4].ink[3] - it[4].base for it in items)
        rows.append((items, lw, top, bot))

    gap = sup["line_gap"] * H
    total = sum(b - t for _, _, t, b in rows) + gap * (len(rows) - 1)
    cyc = sup.get("anchor_cycle")
    ax, ay = cyc[idx % len(cyc)] if cyc else sup["anchor"]
    if has_ih and sup.get("ihero_phrase_anchor"):
        ax, ay = sup["ihero_phrase_anchor"]
    va = sup["valign"]
    y = ay * H - (total / 2 if va == "center" else (total if va == "bottom" else 0))
    stagger = sup.get("stagger") or []
    placed, block = [], [1e9, y, -1e9, y + total]
    for li, (items, lw, top, bot) in enumerate(rows):
        base_y = y - top
        dx = (stagger[li] if li < len(stagger) else 0) * W
        x = (sup.get("left_x", 0.12) * W if sup["align"] == "left" else ax * W - lw / 2) + dx
        for w, spec, txt, sc, s in items:
            placed.append({"w": w, "spec": spec, "txt": txt, "sprite": s, "scale": sc,
                           "x": x - s.ink[0], "y": base_y - s.base})
            block[0], block[2] = min(block[0], x), max(block[2], x + s.ink[2] - s.ink[0])
            x += s.ink[2] - s.ink[0] + spec["size"] * H * sc * sup["word_gap"]
        y += (bot - top) + gap
    return {"items": placed, "block": block}


# --------------------------------------------------------------------------- matte
def matte_model():
    for p in MATTE_MODEL_CANDIDATES:
        if p and os.path.isfile(p):
            return p
    raise SystemExit("[captionfx] u2net_human_seg.onnx not found. Put it in engine/models/ or set "
                     "CAPTIONFX_MATTE_MODEL (see engine/models/README.md), or run with --no-matte.")


def matte_size(info):
    return info["w"] // 4 * 2, info["h"] // 4 * 2


def build_matte(src, info, out_path, every=1):
    import onnxruntime as ort
    sess = ort.InferenceSession(matte_model(), providers=ort.get_available_providers())
    iname = sess.get_inputs()[0].name
    mw = mh = 320
    ow, oh = matte_size(info)
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"scale={mw}:{mh}", "-f", "rawvideo",
                           "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{ow}x{oh}",
                           "-r", str(info["fps"]), "-i", "-", "-c:v", "ffv1", out_path], stdin=subprocess.PIPE)
    mean = np.array([0.485, 0.456, 0.406], np.float32)
    std = np.array([0.229, 0.224, 0.225], np.float32)
    prev, last, i = None, None, 0
    while True:
        buf = rd.stdout.read(mw * mh * 3)
        if len(buf) < mw * mh * 3:
            break
        if last is None or i % every == 0:
            x = np.frombuffer(buf, np.uint8).reshape(mh, mw, 3).astype(np.float32) / 255
            x = (x / max(1e-6, x.max()) - mean) / std
            pred = sess.run(None, {iname: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
            last = (pred - pred.min()) / max(1e-6, pred.max() - pred.min())
        m = last if prev is None else 0.7 * last + 0.3 * prev      # light temporal smoothing
        prev = m
        img = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize((ow, oh), Image.BILINEAR)
        wr.stdin.write(img.tobytes())
        i += 1
        if i % 60 == 0:
            print(f"[matte] {i} frames", flush=True)
    wr.stdin.close()
    wr.wait()
    rd.wait()


class MatteReader:
    def __init__(self, path, info):
        self.w, self.h = matte_size(info)
        self.W, self.H = info["w"], info["h"]
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                                  stdout=subprocess.PIPE)
        self.last = np.zeros((self.H, self.W), np.float32)

    def next(self):
        buf = self.p.stdout.read(self.w * self.h)
        if len(buf) == self.w * self.h:
            m = Image.fromarray(np.frombuffer(buf, np.uint8).reshape(self.h, self.w))
            m = m.resize((self.W, self.H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.0))
            # push soft edges toward solid so text hides cleanly behind hair and shoulders
            self.last = np.clip((np.asarray(m, np.float32) / 255 - 0.2) / 0.5, 0, 1)
        return self.last


# --------------------------------------------------------------------------- drawing helpers
def paste(canvas, img, x, y, alpha=1.0):
    if alpha <= 0.003:
        return
    x, y = int(round(x)), int(round(y))
    if alpha < 0.997:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    W, H = canvas.size
    l, t, r, b = max(0, x), max(0, y), min(W, x + img.width), min(H, y + img.height)
    if r > l and b > t:
        canvas.alpha_composite(img.crop((l - x, t - y, r - x, b - y)), (l, t))


def transform(img, ink, scale=1.0, blur=0.0):
    """Scale around the ink centre and/or blur. Returns (image, (dx, dy))."""
    off = (0.0, 0.0)
    if abs(scale - 1) > 0.004:
        cx, cy = (ink[0] + ink[2]) / 2, (ink[1] + ink[3]) / 2
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BICUBIC)
        off = (cx - cx * scale, cy - cy * scale)
    if blur > 0.3:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    return img, off


def entry_state(entry, u, size):
    """(alpha, dy, scale, blur) for entry progress u in [0, 1]."""
    kind = entry.get("type", "fade")
    e = ease_out(u)
    if kind == "cut" or u >= 1:
        return 1.0, 0.0, 1.0, 0.0
    if kind == "fade":
        return e, 0.0, 1.0, 0.0
    if kind == "rise":
        return e, (1 - e) * size * entry.get("dist", 0.35), 1.0, 0.0
    if kind == "pop":
        return min(1.0, u * 2.5), 0.0, 1 + (entry.get("from", 1.25) - 1) * (1 - ease_out_back(u)), 0.0
    if kind == "blur":
        return e, 0.0, 1 + 0.06 * (1 - e), (1 - e) * size * 0.16
    if kind == "fade_from":
        a0 = entry.get("from", 0.3)
        return a0 + (1 - a0) * e, 0.0, 1.0, 0.0
    return e, 0.0, 1.0, 0.0


def luma(rgb):
    return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255


def spec_luma(spec):
    c = (spec.get("gradient") or [spec.get("color", "#FFFFFF")])[0]
    return luma(hex_rgba(c))


_halo_cache = {}


def halo(sprite, strength=0.85):
    """Dark cloud + tight shadow behind light text so it survives bright backgrounds (white shirts, windows)."""
    key = (id(sprite), strength)
    if key not in _halo_cache:
        a = sprite.img.getchannel("A")
        wide = np.asarray(a.filter(ImageFilter.GaussianBlur(max(3, sprite.size * 0.4))), np.float32)
        tight = np.asarray(a.filter(ImageFilter.GaussianBlur(max(1, sprite.size * 0.08))), np.float32)
        wide = np.clip(wide / max(1.0, wide.max()) * 1.5, 0, 1) * 255     # normalise: thin strokes get a full cloud
        tight = np.clip(tight / max(1.0, tight.max()) * 1.6, 0, 1) * 255
        m = np.maximum(wide * 0.6, tight * 0.85) * strength
        img = Image.new("RGBA", sprite.img.size, (8, 10, 14, 255))
        img.putalpha(Image.fromarray(np.clip(m, 0, 255).astype(np.uint8), "L"))
        _halo_cache[key] = img
    return _halo_cache[key]


def occluded(m, sprite, x, y):
    """Fraction of the text's ink covered by the subject matte."""
    if m is None:
        return 0.0
    H, W = m.shape
    l, t, r, b = sprite.ink
    x0, y0, x1, y1 = int(max(0, x + l)), int(max(0, y + t)), int(min(W, x + r)), int(min(H, y + b))
    if x1 <= x0 or y1 <= y0:
        return 0.0
    a = np.asarray(sprite.img.getchannel("A"), np.float32)[y0 - int(y):y1 - int(y), x0 - int(x):x1 - int(x)] > 64
    reg = m[y0:y1, x0:x1][:a.shape[0], :a.shape[1]]
    return float((reg[a] > 0.5).mean()) if a.any() else 0.0


def dark_spec(spec):
    """Contrast swap for bright backgrounds: white -> near-black, colours -> deep shade. No shadow, no glow."""
    if spec.get("contrast") == "shadow":          # keep the style's colours, lean on a heavy shadow
        return dict(spec, shadow=spec.get("boost_shadow", 0.9))
    rgb = hex_rgba((spec.get("gradient") or [spec.get("color", "#FFFFFF")])[0])[:3]
    dark = "#141414" if luma(rgb) > 0.8 else "#%02X%02X%02X" % tuple(int(c * 0.42) for c in rgb)
    out = dict(spec, color=dark, shadow=0, glow=0)
    out.pop("gradient", None)
    if out.get("active_color"):
        out["active_color"] = "#1E6FB0"
    return out


def needs_boost(frame, sprite, x, y, spec):
    """True when light text would sit on a bright background."""
    if spec_luma(spec) < 0.55 and not spec.get("outline_only"):
        return False
    H, W = frame.shape[:2]
    l, t, r, b = sprite.ink
    x0, y0 = int(max(0, x + l)), int(max(0, y + t))
    x1, y1 = int(min(W, x + r)), int(min(H, y + b))
    if x1 <= x0 or y1 <= y0:
        return False
    reg = frame[y0:y1:2, x0:x1:2].astype(np.float32)
    lum = (0.299 * reg[..., 0] + 0.587 * reg[..., 1] + 0.114 * reg[..., 2]) / 255
    return lum.mean() > 0.45 or (lum > 0.7).mean() > 0.25


# --------------------------------------------------------------------------- speaker tracking + camera
def head_track(matte_path, info, fps):
    """Per-frame head top / centre x / head width (normalised) from the cached matte."""
    sw, sh = 90, 160
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", matte_path, "-vf", f"scale={sw}:{sh}", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
    rows = []
    while True:
        buf = p.stdout.read(sw * sh)
        if len(buf) < sw * sh:
            break
        m = np.frombuffer(buf, np.uint8).reshape(sh, sw) > 127
        occ = m.sum(1) >= 2
        if not occ.any():
            rows.append(rows[-1] if rows else (0.2, 0.5, 0.2))
            continue
        top = int(np.argmax(occ))
        band = m[top:top + int(0.1 * sh)]
        cx = np.nonzero(band)[1].mean() / sw
        r = m[min(sh - 1, top + int(0.06 * sh))]
        xs = np.nonzero(r)[0]
        hw = (xs.max() - xs.min() + 1) / sw if len(xs) else 0.2
        rows.append((top / sh, cx, min(max(hw, 0.08), 0.45)))
    p.wait()
    arr = np.array(rows, np.float32)
    k = max(1, int(fps * 0.5))          # half-second median smoothing: no jitter
    sm = np.array([np.median(arr[max(0, i - k):i + k + 1], axis=0) for i in range(len(arr))])
    return sm


class Camera:
    """Zoom schedule + speaker-aware geometry. All positions normalised to the output frame."""

    def __init__(self, W, H, fps, track=None):
        self.W, self.H, self.fps, self.track = W, H, fps, track
        self.base, self.punch = [], []           # base: (t, zoom), punch: (start, end, amount)
        self.drift = 0.0

    def raw_head(self, t):
        if self.track is None or not len(self.track):
            return 0.2, 0.5, 0.22
        i = min(len(self.track) - 1, max(0, int(t * self.fps)))
        return tuple(float(v) for v in self.track[i])

    def zoom(self, t):
        z, prev, t0, t1 = 1.0, 1.0, 0.0, None
        for i, (ts, zz) in enumerate(self.base):
            if t >= ts:
                prev, z, t0 = z, zz, ts
                t1 = self.base[i + 1][0] if i + 1 < len(self.base) else None
        if t0 > 0 and t - t0 < 0.8:              # glide to the new framing, no hard jump
            z = prev + (z - prev) * ease_out((t - t0) / 0.8)
        if t1:
            z += self.drift * min(1.0, (t - t0) / max(0.1, t1 - t0))
        env = 0.0
        for s, e, amt in self.punch:
            if s <= t < e:
                env = max(env, amt * ease_out((t - s) / 0.5))
            elif e <= t < e + 0.8:
                env = max(env, amt * (1 - ease_out((t - e) / 0.8)))
        return min(1.4, z + env)

    def box(self, t):
        z = self.zoom(t)
        top, cx, hw = self.raw_head(t)
        face_h = hw * 1.35 * self.W / self.H
        cy = top + face_h * 0.55
        w, h = 1 / z, 1 / z
        x0 = min(max(0.0, cx - w / 2), 1 - w)
        y0 = min(max(0.0, cy - h * 0.38), 1 - h)     # keep face in the upper-middle third
        return x0, y0, z

    def head(self, t):
        """Screen-space head: top, centre x, head width, face bottom (normalised)."""
        top, cx, hw = self.raw_head(t)
        x0, y0, z = self.box(t)
        face_h = hw * 1.35 * self.W / self.H
        return {"top": (top - y0) * z, "cx": (cx - x0) * z, "hw": hw * z, "fb": (top + face_h - y0) * z}


def avoid_face(lay, head, W, H, safe_top=0.06, safe_bottom=0.87):
    if not lay:
        return
    l, t, r, b = lay["block"]
    fx0, fx1 = (head["cx"] - head["hw"] * 0.65) * W, (head["cx"] + head["hw"] * 0.65) * W
    fy0, fy1 = (head["top"] - 0.01) * H, (head["fb"] + 0.035) * H
    dy = 0.0
    if r > fx0 and l < fx1 and b > fy0 and t < fy1:
        below = fy1 - t
        above = fy0 - b
        dy = below if fy1 + (b - t) <= safe_bottom * H else above
    if b + dy > safe_bottom * H:
        dy = safe_bottom * H - b
    if t + dy < safe_top * H:
        dy = safe_top * H - t
    if dy:
        for it in lay["items"]:
            it["y"] += dy
        lay["block"] = [l, t + dy, r, b + dy]


# --------------------------------------------------------------------------- render
def render(args):
    st = load_style(args.style)
    src = probe(args.input)
    W = min(src["w"], args.width) // 2 * 2
    H = int(round(src["h"] * W / src["w"])) // 2 * 2
    fps = src["fps"]
    info = dict(src, w=W, h=H)
    work = args.workdir or os.path.splitext(args.output)[0] + "_captionfx"
    os.makedirs(work, exist_ok=True)

    if args.words:
        words = json.load(open(args.words, encoding="utf-8"))
    else:
        if not src["audio"]:
            raise SystemExit("[captionfx] video has no audio track - pass --words words.json")
        print("[captionfx] transcribing...", flush=True)
        words = transcribe(args.input, args.model, args.language)
    json.dump(words, open(os.path.join(work, "words.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    words = copy.deepcopy(words)

    phrases = plan(words, st)
    tm = st["timing"]
    lead = args.lead if args.lead is not None else tm["lead"]
    fx = st["fx"]
    hero = st.get("hero")

    # subject matte (also drives speaker-aware layout and the camera)
    matte_path, track = None, None
    if not args.no_matte:
        matte_path = os.path.join(work, "matte.mkv")
        if not os.path.isfile(matte_path) or args.rematte:
            print("[captionfx] building subject matte...", flush=True)
            build_matte(args.input, info, matte_path, args.matte_every)
        track = head_track(matte_path, info, fps)

    cam = Camera(W, H, fps, track)
    zmode = args.zoom
    if zmode == "style":
        zmode = "auto" if fx.get("punch_in") else "none"
    hero_words = [w for ph in phrases for w in ph if w["role"] == "hero"]
    if zmode == "auto":
        punch_amt = (fx.get("punch_in", {}).get("scale", 1.0 + args.punch) - 1.0)
        sent_starts, new = [], True
        for ph in phrases:
            if new:
                sent_starts.append(ph[0]["s"] - lead)
            new = bool(re.search(r"[.!?]$", ph[-1]["w"]))
        # Calm camera: every zoom move (framing change or punch) is at least
        # --zoom-gap seconds from the last one, about 5-10 moves per minute.
        moves, last = [], -1e9
        for s in sent_starts[1:]:
            moves.append(("cut", s, None))
        for w in hero_words:
            moves.append(("punch", w["s"] - lead, w))
        moves.sort(key=lambda m: m[1])
        cam.base.append((0.0, 1.0))
        framing = 1.0
        for kind, s, w in moves:
            if s - last < args.zoom_gap:
                continue
            if kind == "cut":
                framing = args.alt_zoom if framing == 1.0 else 1.0
                cam.base.append((max(0.0, s), framing))
            else:
                cam.punch.append((s, w["e"] + 0.8, punch_amt))
            last = s
        cam.drift = args.drift

    P = []
    for i, ph in enumerate(phrases):
        start = ph[0]["s"] - lead
        nxt = phrases[i + 1][0]["s"] - lead if i + 1 < len(phrases) else info["dur"]
        end = min(nxt, max(ph[-1]["e"] + tm["hold"], start + tm["min_show"]))
        lay = layout_phrase(ph, st, W, H, i)
        if track is not None and not st["support"].get("allow_face"):
            avoid_face(lay, cam.head(start + 0.3), W, H)
        P.append({"words": ph, "lay": lay, "start": start, "end": end})

    HS = []
    if hero:
        for i, w in enumerate(hero_words):
            spec = role_spec(st, "hero", w)
            if i == len(hero_words) - 1 and hero.get("texture_on_last"):
                spec = dict(spec, texture=hero["texture_on_last"])
            txt = strip_punct(w["w"]) if hero.get("strip_punct", True) else w["w"]
            s = render_text(txt, spec, H)
            mw = spec.get("max_width", hero["max_width"]) * W
            if s.ink[2] - s.ink[0] > mw:
                s = render_text(txt, spec, H, mw / (s.ink[2] - s.ink[0]) * 0.98)
            a = spec.get("anchor", hero["anchor"])
            va = spec.get("valign", hero["valign"])
            rows = hero.get("repeat", 1)
            gap = hero.get("row_gap", 0.004) * H
            iw, ihh = s.ink[2] - s.ink[0], s.ink[3] - s.ink[1]
            start = w["s"] - lead
            x = a[0] * W - iw / 2 - s.ink[0]
            y = a[1] * H - (ihh / 2 if va == "center" else 0) - s.ink[1]
            attach = spec.get("attach", hero.get("attach", "head" if hero.get("behind") and a[1] < 0.35 else None))
            if attach == "head" and track is not None:
                hd = cam.head(start + 0.3)
                ov = hero.get("head_overlap", 0.45)
                block_h = rows * ihh + (rows - 1) * gap
                bottom = hd["top"] * H + ov * ihh
                avail = bottom - 0.015 * H
                if block_h > avail > 0:
                    k = max(0.55, avail / block_h)
                    s = render_text(txt, spec, H, (s.size / (spec["size"] * H)) * k)
                    iw, ihh = s.ink[2] - s.ink[0], s.ink[3] - s.ink[1]
                    block_h = rows * ihh + (rows - 1) * gap
                    bottom = hd["top"] * H + ov * ihh
                x = a[0] * W - iw / 2 - s.ink[0]
                y = max(0.012 * H, bottom - block_h) - s.ink[1]
            HS.append({"w": w, "sprite": s, "spec": spec, "start": start, "txt": txt,
                       "scale": s.size / (spec["size"] * H),
                       "end": min(hero_words[i + 1]["s"] - lead if i + 1 < len(hero_words) else info["dur"],
                                  w["e"] + hero["hold"]),
                       "x": x, "y": y, "row_h": ihh + gap})

    json.dump({"style": st["id"], "size": [W, H], "zoom": zmode,
               "phrases": [{"start": round(p["start"], 3), "end": round(p["end"], 3),
                            "words": [f'{w["w"]}:{w["role"]}' for w in p["words"]]} for p in P],
               "heroes": [{"word": h["w"]["w"], "start": round(h["start"], 3), "end": round(h["end"], 3)} for h in HS]},
              open(os.path.join(work, "plan.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"[captionfx] style={st['id']} {W}x{H} zoom={zmode} {len(P)} phrases, {len(HS)} hero words -> {work}",
          flush=True)
    if args.plan_only:
        return

    need_matte = (hero and hero.get("behind")) or fx.get("subject_outline") or \
        any(r.get("behind") for r in st["roles"].values())
    matte = MatteReader(matte_path, info) if (matte_path and (need_matte or zmode == "auto")) else None

    frames = subprocess.Popen(["ffmpeg", "-v", "error", "-i", args.input, "-vf", f"scale={W}:{H}:flags=lanczos",
                               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    stills = {int(round(float(t) * fps)) for t in args.stills.split(",")} if args.stills else None
    enc = None
    if stills is None:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", args.input,
                                "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-preset", "medium",
                                "-crf", str(args.crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                                "-shortest", "-movflags", "+faststart", args.output], stdin=subprocess.PIPE)
    fi, fb = 0, W * H * 3
    while True:
        buf = frames.stdout.read(fb)
        if len(buf) < fb:
            break
        t = fi / fps
        m = matte.next() if matte else None
        if stills is not None and fi not in stills:
            fi += 1
            continue
        frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        x0, y0, z = cam.box(t)
        if z > 1.001:
            box = (x0 * W, y0 * H, (x0 + 1 / z) * W, (y0 + 1 / z) * H)
            frame = np.asarray(Image.fromarray(frame).resize((W, H), Image.BICUBIC, box=box))
            if m is not None:
                m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR, box=box),
                               np.float32) / 255
        out = compose(frame, m if need_matte else None, t, P, HS, st, W, H, lead)
        if enc:
            enc.stdin.write(out.tobytes())
        else:
            p = os.path.join(work, f"still_{t:06.2f}.png")
            Image.fromarray(out).save(p)
            print(p)
        fi += 1
        if fi % 150 == 0:
            print(f"[render] {fi} frames ({t:.1f}s)", flush=True)
    frames.wait()
    if enc:
        enc.stdin.close()
        enc.wait()
        print(f"[captionfx] done -> {args.output}")


def compose(frame, m, t, P, HS, st, W, H, lead):
    canvas = Image.fromarray(frame).convert("RGBA")
    fx, hero, sup = st["fx"], st.get("hero") or {}, st["support"]
    behind_drawn = False
    active_hero = [h for h in HS if h["start"] <= t < h["end"]]
    active_ph = [p for p in P if p["start"] <= t < p["end"] and p["lay"]]

    so = fx.get("subject_outline")
    if so and m is not None and (active_hero or not so.get("with_hero", True)):
        import cv2
        u = ease_out((t - active_hero[0]["start"]) / 0.25) if active_hero else 1.0
        mb = (m > 0.5).astype(np.uint8)
        r1 = max(1, int(so.get("offset", 0.012) * H))
        r2 = r1 + max(2, int(so.get("width", 0.006) * H))
        k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        ring = (cv2.dilate(mb, k(r2)) - cv2.dilate(mb, k(r1))).astype(np.float32)
        ring = cv2.GaussianBlur(ring, (3, 3), 0)
        lay = np.zeros((H, W, 4), np.uint8)
        lay[..., :3] = hex_rgba(so["color"])[:3]
        lay[..., 3] = np.clip(ring * 255 * u, 0, 255).astype(np.uint8)
        canvas.alpha_composite(Image.fromarray(lay, "RGBA"))
        behind_drawn = True

    def draw_hero(h):
        entry = hero["entry"]
        if "boost" not in h:
            h["boost"] = needs_boost(frame, h["sprite"], h["x"], h["y"], h["spec"])
            if h["boost"]:
                h["spec"] = dark_spec(h["spec"])
                h["sprite"] = render_text(h["txt"], h["spec"], H, h["scale"])
        for r in range(hero.get("repeat", 1)):
            u = (t - h["start"] - r * hero.get("row_delay", 0.08)) / max(0.01, entry.get("dur", 0.2))
            if u < 0:
                continue
            a, dy, sc, bl = entry_state(entry, u, h["sprite"].size)
            ops = hero.get("row_opacity", [1.0, 0.85, 0.7])
            a *= ops[min(r, len(ops) - 1)] * h["spec"].get("layer_opacity", 1.0)
            yy = h["y"] + dy + r * h["row_h"]
            img, off = transform(h["sprite"].img, h["sprite"].ink, sc, bl)
            paste(canvas, img, h["x"] + off[0], yy + off[1], a)

    for h in active_hero:
        if "front" not in h:
            h["front"] = not hero.get("behind") or occluded(m, h["sprite"], h["x"], h["y"]) > hero.get("max_hidden", 0.45)
        if not h["front"]:
            draw_hero(h)
            behind_drawn = True

    glass = fx.get("glass_pill")

    def draw_phrase(p, behind):
        drew = False
        items = p["lay"]["items"]
        for it in items:
            if it["spec"].get("behind", False) != behind:
                continue
            w, s = it["w"], it["sprite"]
            if "boost" not in it:
                it["boost"] = (not glass) and needs_boost(frame, s, it["x"], it["y"], it["spec"])
                if it["boost"]:
                    it["spec"] = dark_spec(it["spec"])
                    it["sprite"] = s = render_text(it["txt"], it["spec"], H, it["scale"])
            ws = w["s"] - lead
            entry = it["spec"].get("entry") or sup["entry"]
            if t < ws:
                pv = it["spec"].get("preview_opacity", sup["preview_opacity"])
                if pv > 0:
                    paste(canvas, s.img, it["x"], it["y"], pv)
                    drew = True
                continue
            if entry.get("type") == "type":
                draw_typewriter(canvas, it, t - ws, entry, H)
                drew = True
                continue
            a, dy, sc, bl = entry_state(entry, (t - ws) / max(0.01, entry.get("dur", 0.16)), s.size)
            spr = s
            act = it["spec"].get("active_color")
            if act:
                later = [x["w"]["s"] for x in items if x["w"]["s"] > w["s"]]
                if t < (later[0] if later else w["e"] + 0.15) - lead:
                    spr = render_text(it["txt"], it["spec"], H, it["scale"], act)
            if sup["exit"]["type"] == "fade":
                a *= min(1.0, max(0.0, (p["end"] - t) / sup["exit"]["dur"]))
            img, off = transform(spr.img, spr.ink, sc, bl)
            paste(canvas, img, it["x"] + off[0], it["y"] + dy + off[1], a)
            drew = True
        return drew

    for p in active_ph:
        behind_drawn |= draw_phrase(p, True)

    if m is not None and behind_drawn:
        c = np.asarray(canvas, np.float32).copy()
        mm = m[..., None]
        c[..., :3] = c[..., :3] * (1 - mm) + frame.astype(np.float32) * mm
        canvas = Image.fromarray(c.astype(np.uint8), "RGBA")

    for h in active_hero:
        if h["front"]:
            draw_hero(h)
    for p in active_ph:
        if glass:
            draw_glass(canvas, p, glass, t, W, H)
        draw_phrase(p, False)
    return np.asarray(canvas.convert("RGB"))


def draw_typewriter(canvas, it, dt, entry, H):
    txt, w = it["txt"], it["w"]
    n = len(txt)
    per = min(entry.get("char_time", 0.045), max(0.012, (w["e"] - w["s"]) / max(1, n)))
    k = min(n, int(dt / per) + 1)
    s = render_text(txt[:k], it["spec"], H, it["scale"])
    x, y = it["x"], it["y"]
    if k < n and entry.get("box"):
        c0, c1 = s.cx[k - 1], s.cx[k]
        box = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle(
            (x + s.ox + c0 - s.size * 0.07, y + s.base - s.size * 0.8, x + s.ox + c1 + s.size * 0.07,
             y + s.base + s.size * 0.2), radius=s.size * 0.18, fill=hex_rgba(entry["box"]))
        canvas.alpha_composite(box)
    paste(canvas, s.img, x, y)


def draw_glass(canvas, p, gp, t, W, H):
    l, tp, r, b = p["lay"]["block"]
    pw = max(r - l + 2 * gp.get("pad_x", 0.05) * W, gp.get("min_width", 0.7) * W)
    ph = (b - tp) + 2 * gp.get("pad_y", 0.022) * H
    cx = gp.get("center_x", 0.5) * W
    x0, y0 = int(max(0, cx - pw / 2)), int(max(0, (tp + b) / 2 - ph / 2))
    x1, y1 = int(min(W, cx + pw / 2)), int(min(H, (tp + b) / 2 + ph / 2))
    u = ease_out((t - p["start"]) / 0.2)
    region = canvas.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(gp.get("blur", 14)))
    bright = np.asarray(region.convert("L"), np.float32).mean() / 255 > 0.55
    tint = hex_rgba(gp.get("dark_tint", "#101418"), gp.get("dark_alpha", 0.38)) if bright else         hex_rgba(gp.get("tint", "#FFFFFF"), gp.get("tint_alpha", 0.2))
    region = Image.alpha_composite(region, Image.new("RGBA", region.size, tint))
    rad = gp.get("radius", 0.35) * (y1 - y0)
    mask = Image.new("L", region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, region.width - 1, region.height - 1), radius=rad, fill=int(255 * u))
    region.putalpha(mask)
    ImageDraw.Draw(region).rounded_rectangle((0, 0, region.width - 1, region.height - 1), radius=rad,
                                             outline=hex_rgba("#FFFFFF", gp.get("border_alpha", 0.35) * u),
                                             width=max(1, H // 640))
    canvas.alpha_composite(region, (x0, y0))


# --------------------------------------------------------------------------- styles
def load_style(name):
    p = name if os.path.isfile(name) else os.path.join(STYLE_DIR, f"{name}.json")
    if not os.path.isfile(p):
        raise SystemExit(f"[captionfx] unknown style '{name}'. Available: {', '.join(list_styles())}")
    st = deep_merge(DEFAULTS, json.load(open(p, encoding="utf-8")))
    specs = list(st["roles"].values()) + ([st["hero"]["spec"]] if st.get("hero") else [])
    for sp in specs:
        if sp.get("shadow"):
            sp["shadow"] = round(sp["shadow"] * 0.3, 3)      # barely-there shadow; contrast comes from colour
    if st.get("hero"):
        st["hero"] = deep_merge(HERO_DEFAULTS, st["hero"])
    return st


def list_styles():
    return sorted(f[:-5] for f in os.listdir(STYLE_DIR) if f.endswith(".json"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?")
    ap.add_argument("--style", "-s")
    ap.add_argument("-o", "--output")
    ap.add_argument("--words", help="words.json to use instead of transcribing")
    ap.add_argument("--model", default="small", help="faster-whisper model: small, medium, large-v3")
    ap.add_argument("--language")
    ap.add_argument("--lead", type=float, help="seconds a word appears before it is spoken (default per style)")
    ap.add_argument("--workdir")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--width", type=int, default=1080, help="output width (keeps aspect); 4K sources render at 1080")
    ap.add_argument("--zoom", choices=["auto", "style", "none"], default="auto",
                    help="auto: camera cuts in/out per sentence + punch-in on key words; style: only styles with punch_in")
    ap.add_argument("--punch", type=float, default=0.12, help="punch-in amount on key words (auto zoom)")
    ap.add_argument("--alt-zoom", type=float, default=1.12, help="zoom of every other sentence (jump-cut feel)")
    ap.add_argument("--drift", type=float, default=0.03, help="slow push-in across each sentence")
    ap.add_argument("--zoom-gap", type=float, default=7.0,
                    help="min seconds between zoom moves (7 = about 8 per minute)")
    ap.add_argument("--stills", help="comma-separated times in seconds: write PNG stills instead of a video")
    ap.add_argument("--plan-only", action="store_true", help="only write words.json + plan.json")
    ap.add_argument("--no-matte", action="store_true", help="skip the subject matte (nothing goes behind the subject)")
    ap.add_argument("--rematte", action="store_true", help="rebuild the cached matte")
    ap.add_argument("--matte-every", type=int, default=1, help="segment every Nth frame (faster)")
    ap.add_argument("--list", action="store_true", help="list styles")
    a = ap.parse_args()
    if a.list or not a.input:
        print("\n".join(list_styles()))
        return
    if not a.style:
        ap.error("--style is required")
    if not a.output:
        a.output = os.path.splitext(a.input)[0] + f"_{os.path.splitext(os.path.basename(a.style))[0]}.mp4"
    render(a)


if __name__ == "__main__":
    main()
