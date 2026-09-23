# Linen

> Dynamic, textured captions with a warm editorial paper feel.

| | |
|---|---|
| Style id (what the order stores) | `dyn-linen` |
| Tier | Captions Only |
| Editing skill | `embedded-captions` |
| Engine style | `dyn-linen` |
| Best for | Founders, consultants, premium personal brands |
| Categories | Dynamic |
| Includes | Designed captions, Retakes removed |
| Website preview | `web/static/previews/dyn-linen.mp4` |
| Style reference | `references/captions/dyn-linen-c7b84c695694.mp4` (private - style DNA only, never show publicly) |

## How to edit an order in this style

1. Transcribe the raw video and remove retakes, false starts and long pauses.
2. Keep the customer's footage as it is - no B-roll, no motion graphics, no tool screens.
3. Apply this style's caption treatment: typography, placement, colours and motion.
4. QC: captions match the spoken words, stay inside safe areas and are readable on a phone.

## Not in this style

No B-roll, no motion graphics, no colour-grade changes beyond what the caption style needs.

## Commands

```bash
python reelflow.py prepare <order_id>   # downloads the raw video, writes ORDER.md with this style
python reelflow.py deliver <order_id> <project>/renders/<order_id>.mp4
```

_Generated from `styles.json` by `tools/build_skill_docs.py` - edit styles.json, not this file._
