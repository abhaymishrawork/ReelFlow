"""Customer website: pick a style, upload a raw video, track the order, download the finished reel.

  python web/app.py            (or start_website.bat)  -> http://localhost:8765
"""
import json, os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask, abort, redirect, render_template, request, send_file, url_for
from core import config, jobs, notify, storage

CFG = config.load()
Q, S = jobs.get(CFG), storage.get(CFG)
ALL_STYLES = CFG["styles"] + CFG["caption_styles"]
STYLE_IDS = {s["id"] for s in ALL_STYLES}
STYLE_BY_ID = {s["id"]: s for s in ALL_STYLES}
TIER_IDS = {t["id"] for t in CFG["tiers"]}

HERE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(HERE, "templates"), static_folder=os.path.join(HERE, "static"))
app.config["MAX_CONTENT_LENGTH"] = CFG["max_upload_mb"] * 1024 * 1024

STATUS_TEXT = {
    "new": ("Received", "Your video is in the queue. Editing usually starts within a few hours."),
    "editing": ("Editing", "Your reel is being edited right now."),
    "done": ("Ready", "Your reel is ready to download."),
    "failed": ("Needs attention", "We hit a problem with this video and will contact you by email."),
}


def probe_seconds(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "format=duration",
                              "-of", "json", path], capture_output=True, text=True, timeout=60).stdout
        return float(json.loads(out)["format"]["duration"])
    except Exception:  # noqa: BLE001 - unreadable file
        return None


def page(**kw):
    return render_template("index.html", cfg=CFG, styles=CFG["styles"], caption_styles=CFG["caption_styles"],
                           tiers=CFG["tiers"], categories=CFG["categories"], currency=PRICING["currency"],
                           ba=CFG["before_after"], style_ids=STYLE_IDS, **kw)


def clean(v, n=600):
    return (v or "").strip()[:n]


PRICING = json.load(open(config.path("pricing.json"), encoding="utf-8"))
PLAN_IDS = {p["id"] for p in PRICING["plans"]}
PLAN_NAME = {p["id"]: p["name"] for p in PRICING["plans"]}
PLAN_TIER = {p["id"]: p["tier"] for p in PRICING["plans"]}


@app.get("/pricing")
def pricing():
    return render_template("pricing.html", cfg=CFG, pricing=PRICING)


@app.get("/how-it-works")
def how():
    return render_template("how.html", cfg=CFG)


@app.get("/terms")
def terms():
    return render_template("legal.html", cfg=CFG, kind="terms", title="Terms of service", updated="17 Sep 2026")


@app.get("/privacy")
def privacy():
    return render_template("legal.html", cfg=CFG, kind="privacy", title="Privacy policy", updated="17 Sep 2026")


@app.get("/")
def home():
    plan = request.args.get("plan", "")
    tier = request.args.get("tier", "")
    return page(picked=request.args.get("style", ""), plan=plan if plan in PLAN_IDS else "basic",
                plan_name=PLAN_NAME.get(plan, ""),
                tier=tier if tier in TIER_IDS else (PLAN_TIER.get(plan, "")))


@app.post("/order")
def create_order():
    f = request.files.get("video")
    style = request.form.get("style")
    email = clean(request.form.get("email"), 200)
    err = None
    if style not in STYLE_IDS:
        err = "Please choose an editing style."
    elif not f or not f.filename:
        err = "Please choose a video file."
    elif os.path.splitext(f.filename)[1].lower() not in CFG["allowed_ext"]:
        err = "Please upload an MP4, MOV, M4V, MKV or WEBM file."
    elif not clean(request.form.get("name")):
        err = "Please add your name."
    elif "@" not in email or "." not in email.split("@")[-1]:
        err = "Please enter a valid email so we can send your reel."
    elif not request.form.get("consent"):
        err = "Please confirm you own the rights to this video."
    if err:
        return page(picked=style or "", error=err, form=request.form), 400

    oid = Q.new_id()
    key = S.save_upload(oid, f.stream, f.filename)
    local = S.local_path(oid, key)
    secs = probe_seconds(local) if local else None
    limit = CFG["max_video_minutes"] * 60
    if secs is None or secs < CFG["min_video_seconds"] or secs > limit + 1:
        shutil.rmtree(os.path.join(config.path(CFG["storage"]["dir"]), oid), ignore_errors=True)
        msg = ("We couldn't read that video. Please upload an MP4 or MOV file." if secs is None else
               "Your video is %d:%02d long. Please upload a video between %d seconds and %d minutes."
               % (secs // 60, secs % 60, CFG["min_video_seconds"], CFG["max_video_minutes"]))
        return page(picked=style, error=msg, form=request.form), 400
    order = Q.create(oid, {
        "style": style,
        "tier": STYLE_BY_ID[style]["tier"],
        "plan": request.form.get("plan") if request.form.get("plan") in PLAN_IDS else "basic",
        "customer": {"name": clean(request.form.get("name"), 120), "email": email},
        "brief": {
            "audience": clean(request.form.get("audience")),
            "goal": clean(request.form.get("goal")),
            "tools": clean(request.form.get("tools")),
            "language": clean(request.form.get("language"), 40) or "en",
            "notes": clean(request.form.get("notes"), 1500),
        },
        "video": {"key": key, "original_name": clean(f.filename, 200), "seconds": round(secs, 1),
                  "size_mb": round(os.path.getsize(S.local_path(oid, key)) / 1e6, 1) if S.local_path(oid, key) else None},
    })
    style_name = STYLE_BY_ID[style]["name"]
    notify.owner("New reel order", "%s | %s (%s) | %s MB" % (oid, style_name, order["tier"], order["video"]["size_mb"]), CFG)
    return redirect(url_for("order_page", oid=oid, new=1))


@app.get("/order/<oid>")
def order_page(oid):
    o = Q.get(oid)
    if not o:
        abort(404)
    label, text = STATUS_TEXT[o["status"]]
    out = o.get("output")
    link = S.output_url(oid, out["key"]) if o["status"] == "done" and out else None
    style = STYLE_BY_ID.get(o["style"])
    return render_template("order.html", cfg=CFG, o=o, label=label, text=text, link=link, style=style,
                           is_new=request.args.get("new"))


@app.get("/download/<oid>/<key>")
def download(oid, key):
    o = Q.get(oid)
    if not o or o["status"] != "done" or not o.get("output") or o["output"]["key"] != key:
        abort(404)
    p = S.local_path(oid, key)
    if not p:
        abort(404)
    return send_file(p, as_attachment=True, download_name=key.replace("final_", "", 1))


@app.errorhandler(413)
def too_big(_):
    return page(picked="", error="That file is larger than %d MB." % CFG["max_upload_mb"]), 413


@app.errorhandler(404)
def not_found(_):
    return render_template("order.html", cfg=CFG, o=None), 404


if __name__ == "__main__":
    from waitress import serve  # production-grade server that works on Windows

    print("ReelFlow website on http://localhost:%d" % CFG["port"])
    serve(app, host=CFG["host"], port=CFG["port"], threads=8, max_request_body_size=app.config["MAX_CONTENT_LENGTH"])
