"""Regenerates skills/ - one README per editing style the website sells, plus an index.

  python tools/build_skill_docs.py

Source of truth is styles.json. Re-run after adding or renaming a style so the docs never drift from the site.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "skills")

TIER = {
    "full": {
        "label": "Full Edit",
        "skill": "premium-motion-graphics-editor",
        "steps": [
            "Transcribe the raw video and remove retakes, false starts and long pauses.",
            "Work out the audience, goal and CTA from the transcript (the customer brief only refines it).",
            "Cut to a fast 9:16 pace. Add audience-matched real B-roll, real tool logos and real website screens.",
            "Add motion graphics and headlines behind the speaker in this style's look.",
            "Apply this style's caption design, colour grade, soft sound design and ducked music.",
            "QC: video + audio present, 1080x1920, captions readable, no leftover retakes.",
        ],
        "not": "Stock B-roll and logo downloads still need the owner's one batched approval per order.",
    },
    "captions": {
        "label": "Captions Only",
        "skill": "embedded-captions",
        "steps": [
            "Transcribe the raw video and remove retakes, false starts and long pauses.",
            "Keep the customer's footage as it is - no B-roll, no motion graphics, no tool screens.",
            "Apply this style's caption treatment: typography, placement, colours and motion.",
            "QC: captions match the spoken words, stay inside safe areas and are readable on a phone.",
        ],
        "not": "No B-roll, no motion graphics, no colour-grade changes beyond what the caption style needs.",
    },
}


def style_doc(s, cats):
    t = TIER[s["tier"]]
    ref = s.get("reference")
    lines = [
        "# %s" % s["name"],
        "",
        "> %s" % s["tagline"],
        "",
        "| | |",
        "|---|---|",
        "| Style id (what the order stores) | `%s` |" % s["id"],
        "| Tier | %s |" % t["label"],
        "| Editing skill | `%s` |" % t["skill"],
        "| Engine style | `%s` |" % s.get("engine_style", s["id"]),
        "| Best for | %s |" % s["best_for"],
        "| Categories | %s |" % ", ".join(cats.get(c, c) for c in s["categories"]),
        "| Includes | %s |" % ", ".join(s["includes"]),
        "| Website preview | `web/static/%s` |" % s["preview"],
        "| Style reference | %s |" % ("`%s` (private - style DNA only, never show publicly)" % ref if ref else "none - use the house look for this style"),
        "",
        "## How to edit an order in this style",
        "",
    ]
    lines += ["%d. %s" % (i, step) for i, step in enumerate(t["steps"], 1)]
    lines += [
        "",
        "## Not in this style",
        "",
        t["not"],
        "",
        "## Commands",
        "",
        "```bash",
        "python reelflow.py prepare <order_id>   # downloads the raw video, writes ORDER.md with this style",
        "python reelflow.py deliver <order_id> <project>/renders/<order_id>.mp4",
        "```",
        "",
        "_Generated from `styles.json` by `tools/build_skill_docs.py` - edit styles.json, not this file._",
        "",
    ]
    return "\n".join(lines)


def index_doc(styles, cats):
    lines = [
        "# ReelFlow editing styles",
        "",
        "Every style a customer can pick on the website. When an order comes in, its `style` field holds the",
        "**Style id** below - open that style's README to see exactly what to deliver.",
        "",
        "Two tiers:",
        "",
        "- **Full Edit** - retakes removed, real B-roll, tool screens, motion graphics and designed captions.",
        "  Edited with the `premium-motion-graphics-editor` skill.",
        "- **Captions Only** - retakes removed and designed captions on the customer's own footage. Nothing else.",
        "  Edited with the `embedded-captions` skill.",
        "",
    ]
    for tier in ("full", "captions"):
        lines += ["## %s" % TIER[tier]["label"], "", "| Style | Style id | Best for | Look |", "|---|---|---|---|"]
        for s in styles:
            if s["tier"] == tier:
                lines.append("| [%s](%s/README.md) | `%s` | %s | %s |" % (s["name"], s["id"], s["id"], s["best_for"], s["tagline"]))
        lines.append("")
    lines += [
        "## Finding an order's style",
        "",
        "```bash",
        "python reelflow.py list          # the 4th column is the style id",
        "```",
        "",
        "## Adding or changing a style",
        "",
        "1. Edit `styles.json` (and add the preview video to `web/static/previews/`).",
        "2. Run `python tools/build_skill_docs.py` to regenerate this folder.",
        "3. Commit both.",
        "",
        "_Generated from `styles.json` by `tools/build_skill_docs.py`._",
        "",
    ]
    return "\n".join(lines)


def main():
    lib = json.load(open(os.path.join(ROOT, "styles.json"), encoding="utf-8"))
    cats = {c["id"]: c["label"] for c in lib["categories"]}
    styles = lib["styles"] + lib["caption_styles"]
    for s in styles:
        os.makedirs(os.path.join(OUT, s["id"]), exist_ok=True)
        with open(os.path.join(OUT, s["id"], "README.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(style_doc(s, cats))
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(index_doc(styles, cats))
    print("wrote %d style docs to %s" % (len(styles), OUT))


if __name__ == "__main__":
    main()
