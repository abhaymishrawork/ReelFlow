# Gold Premium

> Luxury gold captions, headlines behind you, cinematic warm grade.

| | |
|---|---|
| Style id (what the order stores) | `gold` |
| Tier | Full Edit |
| Editing skill | `premium-motion-graphics-editor` |
| Engine style | `gold` |
| Best for | Founders, consultants, high-ticket services |
| Categories | Business, Coaches |
| Includes | Motion graphics, Real B-roll, Tool screens, Sound design |
| Website preview | `web/static/previews/gold.mp4` |
| Style reference | none - use the house look for this style |

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
