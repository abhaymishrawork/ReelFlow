"""Regenerate engine/styles/*.json. Edit the style values here, then run: python tools/build_styles.py

Each style was measured from its reference clip in references/captions/. Sizes are fractions of the
frame HEIGHT, anchors are [x, y] fractions of the frame. See ../../styles/<id>/SKILL.md for the analysis.
"""
import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "styles")

# Font stacks: exact Google font first (drop it into engine/fonts/), then the closest installed fallback.
SERIF_I = ["PlayfairDisplay-Italic-VF.ttf@Italic", "PlayfairDisplay-Italic.ttf", "BOD_I.TTF", "georgiai.ttf", "DejaVuSerif-Italic.ttf"]
SERIF_BI = ["PlayfairDisplay-Italic-VF.ttf@Bold Italic", "PlayfairDisplay-BoldItalic.ttf", "BOD_BI.TTF", "georgiaz.ttf", "DejaVuSerif-BoldItalic.ttf"]
SCRIPT = ["GreatVibes-Regular.ttf", "PinyonScript-Regular.ttf", "KUNSTLER.TTF", "VIVALDII.TTF"]
HAND = ["GochiHand-Regular.ttf", "PatrickHand-Regular.ttf", "Inkfree.ttf", "segoepr.ttf"]
CSCRIPT = ["DancingScript-VF.ttf@Bold", "DancingScript-Bold.ttf", "Sacramento-Regular.ttf", "segoesc.ttf", "Pacifico-Regular.ttf"]
ANTON = ["Anton-Regular.ttf", "impact.ttf"]
HBLACK = ["HelveticaNeueBlack.otf", "ArchivoBlack-Regular.ttf", "ariblk.ttf"]
HHEAVY = ["HelveticaNeueHeavy.otf", "HelveticaNeueBold.otf", "ariblk.ttf"]
HMED = ["HelveticaNeueMedium.otf", "Inter-VF.ttf@Medium", "Inter-Medium.ttf", "arial.ttf"]
INTER = ["Inter-VF.ttf@Regular", "Inter-Regular.ttf", "HelveticaNeueRoman.otf", "segoeui.ttf"]
MXB = ["Montserrat-ExtraBold.otf", "Montserrat-ExtraBold.ttf", "arialbd.ttf"]
MB = ["Montserrat-Bold.otf", "Montserrat-Bold.ttf", "arialbd.ttf"]
CHALK = ["CabinSketch-Bold.ttf", "GOTHICB.TTF", "arialbd.ttf"]
SERIF = ["LibreCaslonText-VF.ttf@Regular", "LibreCaslonText-Regular.ttf", "georgia.ttf", "times.ttf"]


def POP(w):
    return [f"Poppins-{w}.ttf", "arialbd.ttf"]


S = {}
S["agent-story"] = {
    "name": "Agent Story",
    "grouping": {"max_words": 3, "max_chars": 18, "break_gap": 0.35},
    "support": {"anchor": [0.5, 0.42], "max_per_line": 2, "accent_rule": "content",
                "entry": {"type": "pop", "dur": 0.2, "from": 1.3}},
    "roles": {"base": {"font": POP("SemiBold"), "size": 0.03, "color": "#FFFFFF", "shadow": 0.45},
              "minor": {"font": POP("Medium"), "size": 0.021, "color": "#FFFFFF", "shadow": 0.45},
              "accent": {"font": POP("ExtraBold"), "size": 0.034, "color": "#EEF25A", "shadow": 0.45}},
    "hero": {"pick": "score", "min_score": 5, "min_gap": 1.6, "hold": 1.8, "behind": True,
             "anchor": [0.5, 0.075], "valign": "top", "max_width": 0.8,
             "entry": {"type": "pop", "dur": 0.25, "from": 1.15},
             "spec": {"font": POP("Black"), "size": 0.13, "case": "lower",
                      "gradient": ["#2D7A1F", "#3F9A2C"], "angle": 90},
             "number_spec": {"font": POP("ExtraBold"), "size": 0.1, "outline_only": True, "stroke": 0.022,
                             "gradient": ["#E4EE7A", "#C8D85A"], "anchor": [0.5, 0.47], "valign": "center",
                             "max_width": 0.95}},
}
S["aura"] = {
    "name": "Aura",
    "grouping": {"max_words": 2, "max_chars": 20, "break_gap": 0.35},
    "support": {"anchor": [0.5, 0.78], "max_per_line": 3, "entry": {"type": "fade", "dur": 0.2}},
    "roles": {"base": {"font": SERIF_I, "size": 0.033, "color": "#FFFFFF", "shadow": 0.3, "active_color": "#8CCBF2"}},
    "hero": {"pick": "score", "min_score": 4, "min_gap": 1.2, "hold": 2.6, "behind": True,
             "anchor": [0.5, 0.215], "max_width": 0.9, "entry": {"type": "fade", "dur": 0.25},
             "spec": {"font": HBLACK, "size": 0.1, "case": "upper", "color": "#86C5F0"}},
}
S["chalk"] = {
    "name": "Chalk",
    "grouping": {"max_words": 3, "max_chars": 18, "break_gap": 0.4},
    "support": {"anchor": [0.5, 0.6], "max_per_line": 2, "accent_rule": "content", "preview_opacity": 0.3,
                "entry": {"type": "fade", "dur": 0.18}},
    "roles": {"base": {"font": HAND, "size": 0.036, "color": "#FFFFFF", "shadow": 0.35},
              "accent": {"font": HAND, "size": 0.04, "color": "#F9C80E", "shadow": 0.35}},
    "hero": {"pick": "score", "min_score": 6, "min_gap": 3.0, "hold": 2.8, "behind": True,
             "anchor": [0.5, 0.02], "valign": "top", "max_width": 0.98,
             "repeat": 3, "row_gap": 0.006, "row_delay": 0.1, "row_opacity": [1.0, 0.85, 0.7],
             "entry": {"type": "fade", "dur": 0.3},
             "spec": {"font": CHALK, "size": 0.075, "case": "upper", "color": "#F4F4F0", "texture": "chalk"}},
    "fx": {"subject_outline": {"color": "#F5C400", "offset": 0.012, "width": 0.006, "with_hero": True}},
}
S["dyn-linen"] = {
    "name": "Linen",
    "grouping": {"max_words": 5, "max_chars": 24, "break_gap": 0.5},
    "support": {"anchor": [0.5, 0.72], "valign": "top", "max_per_line": 2, "line_gap": 0.004, "word_gap": 0.3,
                "entry": {"type": "type", "char_time": 0.045, "box": "#FFFFFF70"}},
    "roles": {"base": {"font": HMED, "size": 0.032, "color": "#FFFFFF", "tracking": -0.035, "shadow": 0.4}},
}
S["dyn-quill"] = {
    "name": "Quill",
    "grouping": {"max_words": 4, "max_chars": 24, "break_gap": 0.45},
    "support": {"anchor": [0.5, 0.785], "valign": "top", "max_per_line": 2, "preview_opacity": 0.35,
                "line_gap": 0.0, "entry": {"type": "fade", "dur": 0.18}},
    "roles": {"base": {"font": INTER, "size": 0.029, "color": "#FFFFFF", "shadow": 0.35}},
    "hero": {"pick": "first", "min_gap": 0.0, "hold": 3.0, "behind": False, "anchor": [0.5, 0.72],
             "max_width": 0.92, "entry": {"type": "blur", "dur": 0.35},
             "spec": {"font": SCRIPT, "size": 0.16, "case": "title", "color": "#FFFFFF", "shadow": 0.25}},
}
S["dyn-storyline"] = {
    "name": "Storyline",
    "grouping": {"max_words": 4, "max_chars": 26, "break_gap": 0.45},
    "inline_hero": {"pick": "score", "min_score": 4},
    "support": {"layout": "stack", "anchor": [0.5, 0.7], "valign": "top", "line_gap": 0.002,
                "preview_opacity": 0.3, "entry": {"type": "blur", "dur": 0.25}},
    "roles": {"base": {"font": INTER, "size": 0.023, "color": "#FFFFFF", "shadow": 0.4},
              "minor": {"font": SERIF_I, "size": 0.042, "color": "#FBF1E3", "shadow": 0.3},
              "ihero": {"font": SERIF_BI, "size": 0.07, "color": "#FBF1E3", "shadow": 0.3}},
}
S["ghostline"] = {
    "name": "Ghostline",
    "grouping": {"max_words": 3, "max_chars": 18, "break_gap": 0.4},
    "support": {"anchor": [0.5, 0.72], "valign": "top", "max_per_line": 2,
                "entry": {"type": "pop", "dur": 0.15, "from": 1.2}},
    "roles": {"base": {"font": HHEAVY, "size": 0.03, "color": "#FFFFFF", "shadow": 0.5}},
    "hero": {"pick": "score", "min_score": 5, "min_gap": 1.5, "hold": 2.5, "behind": True,
             "anchor": [0.5, 0.18], "max_width": 0.92, "texture_on_last": "distress",
             "entry": {"type": "pop", "dur": 0.22, "from": 1.12},
             "spec": {"font": HBLACK, "size": 0.075, "color": "#FFFFFF", "shadow": 0.2}},
    "fx": {"punch_in": {"scale": 1.3, "center": [0.5, 0.3], "dur": 0.35}},
}
S["liquid-glass"] = {
    "name": "Liquid Glass",
    "grouping": {"max_words": 3, "max_chars": 22, "break_gap": 0.4},
    "support": {"anchor": [0.5, 0.78], "align": "left", "left_x": 0.2, "max_per_line": 4,
                "entry": {"type": "rise", "dur": 0.2, "dist": 0.25}},
    "roles": {"base": {"font": INTER, "size": 0.025, "color": "#FFFFFF", "tracking": 0.02, "shadow": 0.15}},
    "fx": {"glass_pill": {"min_width": 0.72, "pad_x": 0.045, "pad_y": 0.02, "radius": 0.35, "blur": 16,
                          "tint": "#FFFFFF", "tint_alpha": 0.2, "border_alpha": 0.35}},
}
S["magenta-estate"] = {
    "name": "Magenta Estate",
    "grouping": {"max_words": 4, "max_chars": 24, "break_gap": 0.4},
    "inline_hero": {"pick": "sentence_end"},
    "support": {"anchor": [0.5, 0.52], "max_per_line": 3, "entry": {"type": "pop", "dur": 0.2, "from": 1.25}},
    "roles": {"base": {"font": POP("SemiBold"), "size": 0.024, "color": "#FFFFFF", "shadow": 0.45},
              "minor": {"font": POP("BoldItalic"), "size": 0.02, "color": "#FFFFFF", "shadow": 0.45},
              "ihero": {"font": POP("ExtraBoldItalic"), "size": 0.04, "color": "#FFFFFF", "strip_punct": True,
                        "pill": {"gradient": ["#B516D6", "#E040B8"], "glow": "#E03CD8", "radius": 0.35,
                                 "pad": [0.3, 0.12]}}},
    "hero": {"pick": "score", "min_score": 5, "min_gap": 1.8, "hold": 2.6, "behind": True,
             "anchor": [0.5, 0.2], "max_width": 0.82, "entry": {"type": "pop", "dur": 0.25, "from": 1.15},
             "spec": {"font": POP("Black"), "size": 0.11, "case": "lower",
                      "gradient": ["#4B2BD8", "#9B2BE0", "#D21FCB"], "angle": 35, "glow": 0.25,
                      "glow_color": "#B02FE0"},
             "number_spec": {"font": POP("Black"), "size": 0.1, "gradient": ["#C21FD0", "#7B2FF7"], "angle": 0,
                             "anchor": [0.5, 0.12]}},
}
S["ml-aura"] = {
    "name": "Minimal Aura",
    "grouping": {"max_words": 4, "max_chars": 22, "break_gap": 0.45},
    "support": {"layout": "lines", "line_roles": ["l1", "l2", "l3"], "anchor": [0.5, 0.78],
                "stagger": [-0.05, 0.0, 0.04], "line_gap": 0.005, "preview_opacity": 0.3,
                "entry": {"type": "fade", "dur": 0.2}},
    "roles": {"base": {"font": MXB, "size": 0.028, "case": "upper", "color": "#FFFFFF", "shadow": 0.3},
              "l1": {"font": MXB, "size": 0.027, "case": "upper", "color": "#7EC8F7", "shadow": 0.25},
              "l2": {"font": MXB, "size": 0.027, "case": "upper", "color": "#FFFFFF", "shadow": 0.3},
              "l3": {"font": SERIF_I, "size": 0.046, "color": "#FFFFFF", "shadow": 0.3}},
}
S["ml-blockbuster"] = {
    "name": "Blockbuster",
    "grouping": {"max_words": 4, "max_chars": 24, "break_gap": 0.45},
    "support": {"anchor": [0.5, 0.72], "max_per_line": 3, "entry": {"type": "fade", "dur": 0.2}},
    "roles": {"base": {"font": CSCRIPT, "size": 0.034, "color": "#FFFFFF", "shadow": 0.4}},
    "hero": {"pick": "score", "min_score": 5, "min_gap": 1.5, "hold": 2.8, "behind": True,
             "anchor": [0.5, 0.72], "max_width": 0.78, "entry": {"type": "fade", "dur": 0.3},
             "spec": {"font": ANTON, "size": 0.1, "case": "upper",
                      "gradient": ["#D91F2B", "#E8475A", "#F6A3B4"], "angle": 20, "opacity": 0.95}},
}
S["monument"] = {
    "name": "Monument",
    "grouping": {"max_words": 2, "max_chars": 18, "break_gap": 0.4},
    "support": {"anchor": [0.5, 0.045], "valign": "top", "max_per_line": 3, "accent_rule": "alternate",
                "entry": {"type": "fade", "dur": 0.2}},
    "roles": {"base": {"font": HAND, "size": 0.03, "color": "#FFFFFF", "shadow": 0.3},
              "accent": {"font": HAND, "size": 0.03, "color": "#86F02C", "shadow": 0.3}},
    "hero": {"pick": "score", "min_score": 4, "min_gap": 0.9, "hold": 3.0, "behind": True,
             "anchor": [0.5, 0.175], "max_width": 0.95, "entry": {"type": "fade_from", "dur": 0.35, "from": 0.3},
             "spec": {"font": ANTON, "size": 0.085, "case": "upper", "color": "#86F02C"}},
}
S["play-cursive"] = {
    "name": "Playful Cursive",
    "grouping": {"max_words": 3, "max_chars": 20, "break_gap": 0.4},
    "inline_hero": {"pick": "score", "min_score": 5, "min_gap": 2.2},
    "support": {"anchor": [0.5, 0.05], "valign": "top", "max_per_line": 3, "preview_opacity": 0.35,
                "ihero_phrase_anchor": [0.5, 0.42], "ihero_phrase_scale": 1.6, "line_gap": 0.003,
                "entry": {"type": "fade", "dur": 0.18}},
    "roles": {"base": {"font": MB, "size": 0.024, "color": "#FFFFFF", "shadow": 0.35},
              "ihero": {"font": CSCRIPT, "size": 0.03, "color": "#F3EFA6", "shadow": 0.3,
                        "entry": {"type": "blur", "dur": 0.3}}},
}
S["sunburst"] = {
    "name": "Sunburst",
    "grouping": {"max_words": 4, "max_chars": 26, "break_gap": 0.4},
    "support": {"anchor": [0.5, 0.8], "max_per_line": 5, "accent_rule": "content", "word_gap": 0.35,
                "entry": {"type": "fade", "dur": 0.12}},
    "roles": {"base": {"font": SERIF, "size": 0.026, "color": "#F5E94A", "tracking": 0.05, "shadow": 0.45},
              "accent": {"font": ANTON, "size": 0.034, "case": "upper", "color": "#FFF200", "shadow": 0.45}},
    "hero": {"pick": "score", "min_score": 4, "min_gap": 0.9, "hold": 1.0, "behind": True,
             "anchor": [0.5, 0.005], "valign": "top", "max_width": 0.97, "entry": {"type": "cut"},
             "spec": {"font": ANTON, "size": 0.16, "case": "upper", "color": "#FFF200"}},
}
S["swiss"] = {
    "name": "Swiss",
    "grouping": {"max_words": 3, "max_chars": 22, "break_gap": 0.45},
    "inline_hero": {"pick": "last"},
    "support": {"anchor": [0.5, 0.62], "max_per_line": 3, "line_gap": -0.002, "entry": {"type": "fade", "dur": 0.15}},
    "roles": {"base": {"font": POP("Bold"), "size": 0.026, "case": "lower", "color": "#FFFFFF", "shadow": 0.4,
                       "strip_punct": True},
              "ihero": {"font": POP("Bold"), "size": 0.046, "case": "upper", "color": "#FFD21F", "shadow": 0.4,
                        "strip_punct": True, "entry": {"type": "pop", "dur": 0.2, "from": 1.2}}},
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for k, v in S.items():
        with open(os.path.join(OUT, f"{k}.json"), "w", encoding="utf-8") as f:
            json.dump({"id": k, **v}, f, indent=1)
    print(f"wrote {len(S)} styles to {os.path.normpath(OUT)}")
