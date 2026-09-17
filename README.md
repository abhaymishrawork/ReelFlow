# ReelFlow

Customers pick an editing style, upload a raw talking video, and download a finished reel.
Right now everything runs on this PC and the editing is done by Claude with the
`premium-motion-graphics-editor` skill. Every part can be switched later in `config.json`.

## Daily use

1. Double-click `start_website.bat` and keep the window open. The site is at http://localhost:8765.
2. A customer places an order. A Windows pop-up appears (plus any other channels you turned on).
3. Open Claude Code and say: **"process the next ReelFlow order"**.
4. Claude runs `python reelflow.py next`, edits the video with the chosen style, checks it, and runs
   `python reelflow.py deliver <id> <file>`.
5. The customer's order page switches to **Ready** with a download button.

## Order commands

```
python reelflow.py list            all orders          (list new / editing / done / failed)
python reelflow.py next            claim oldest new order, build projects/<id>/ with raw video + ORDER.md
python reelflow.py deliver ID FILE publish the reel, mark done
python reelflow.py fail ID "why"   mark failed
python reelflow.py watch           repeat a reminder while orders wait
```

## Folders

| Folder | Contents |
|---|---|
| `orders/<id>/` | `order.json`, the customer's raw upload, the delivered reel |
| `projects/<id>/` | Claude's editing project (plan.py, work/, broll/, renders/) |
| `web/static/previews/` | style preview videos shown on the site |

## What you can switch (config.json)

| Part | Now | Later options |
|---|---|---|
| Website hosting | this PC (`start_website.bat`) | same app on a VPS, or behind a Cloudflare Tunnel |
| Public link | `public_url` = localhost | your tunnel or domain URL |
| Order queue | `queue.provider = local` (JSON files) | add a Supabase/Firebase class in `core/jobs.py` |
| Video storage | `storage.provider = local` | `r2` (Cloudflare R2, implemented, untested) |
| Notifications | `desktop`, `log` | `ntfy` (phone push), `telegram`, `email` |
| Customer email on delivery | off | `email_customer_on_delivery: true` + `REELFLOW_RESEND_API_KEY` env var |
| Editor | `claude` (you trigger it) | automatic local worker (open-source model) |

Secrets are never written in `config.json`: values like `env:REELFLOW_NTFY_TOPIC` are read from environment variables.

## Add a new style

1. Add a preset to `STYLES` in the skill's `scripts/render.py`.
2. Render a preview: `set PMGE_STYLE=<id>` then `python render.py <sample project> --until 18`.
3. Make the web preview: `python make_preview.py <render.mp4> <id>`.
4. Add it to `styles.json` → `styles`: `id`, `name`, `categories` (ids from `categories`), `tagline`, `best_for`,
   `includes`, `preview`, `poster`, `engine_style` (renderer preset) and `reference`.
   `reference` = a private sample video (e.g. `references/<file>.mp4`) whose editing look Claude copies when an order
   uses this style. It is never shown on the website.
5. New category: add `{ "id", "label" }` to `categories`. Tabs appear automatically.

Video limits live in `config.json`: `min_video_seconds`, `max_video_minutes`, `max_upload_mb` (checked in the browser and again on the server).

## Before real customers

- **Public access:** customers can't reach `localhost`. Use a Cloudflare Tunnel (free) or a small server, then set `public_url`.
- **Payment:** not built yet. Add a Razorpay/Stripe payment link before the upload step.
- **Preview consent:** the previews use the Nitesh Sureka reel. Get his permission before showing it publicly, or render previews from your own video.
- **Terms and privacy page:** state what you do with uploads and when they are deleted.
