# Swiss Clean

> Minimal black-on-white key words, tight grid captions, no noise.

| | |
|---|---|
| Style id (what the order stores) | `swiss-clean` |
| Tier | Full Edit |
| Editing skill | `premium-motion-graphics-editor` |
| Engine style | `swiss-clean` |
| Best for | Consultants, SaaS founders, clean personal brands |
| Categories | Business, Creators |
| Includes | Motion graphics, Real B-roll, Tool screens, Sound design |
| Website preview | `web/static/previews/swiss-clean.mp4` |
| Style reference | `references/captions/swiss-1cd8e8fdebb0.mp4` (private - style DNA only, never show publicly) |

## How to edit an order in this style

1. Transcribe the raw video and remove retakes, false starts and long pauses.
2. Work out the audience, goal and CTA from the transcript (the customer brief only refines it).
3. Cut to a fast 9:16 pace. Add audience-matched real B-roll, real tool logos and real website screens.
4. Add motion graphics and headlines behind the speaker in this style's look.
5. Apply this style's caption design, colour grade, soft sound design and ducked music.
6. QC: video + audio present, 1080x1920, captions readable, no leftover retakes.

## Not in this style

Stock B-roll and logo downloads still need the owner's one batched approval per order.

## Commands

```bash
python reelflow.py prepare <order_id>   # downloads the raw video, writes ORDER.md with this style
python reelflow.py deliver <order_id> <project>/renders/<order_id>.mp4
```

_Generated from `styles.json` by `tools/build_skill_docs.py` - edit styles.json, not this file._
