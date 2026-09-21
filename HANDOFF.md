# ReelFlow — project handoff (read this first in a new session)

Last updated: 2026-09-17 (third pass: pricing restructured to 3 flat tiers Basic/Creator/Custom, all pricing removed
from the home page, 2 more Full Edit style previews added, "How it works" got real icons + a connecting line).
Owner email to mention: abhayworkofficial@gmail.com only. **Name decision: staying "ReelFlow"** — user asked for
one-word rename ideas (suggested: Reelvet, Reelique, Cutlume, Cutforge, Glintcut, Sparkcut, Reelmint, Klipzy, Reelora),
then explicitly said "don't change the name" — do not rename anything unless the user brings a specific new name.

## What it is
A done-for-you reel editing SaaS with **two tiers**:
- **Full Edit** — retakes removed, motion graphics, real B-roll, real tool logos/screens, captions, music, grade.
  Edited by Claude with the `premium-motion-graphics-editor` skill. Priced higher (creative work, more revisions).
- **Captions Only** — retakes removed, premium designed captions on the raw footage, no B-roll/motion graphics.
  Edited by Claude with the `embedded-captions` skill. Priced lower (fewer subjective choices, fewer revision rounds).
Customer picks a tier + a style within it, uploads a raw talking-head video, downloads the finished reel.
Orders are handled with the `reelflow-orders` skill, which routes to the right editing skill by `order["tier"]`.

Target audience: Indian business owners, founders, coaches, creators. Look: premium, simple, few options.

## Where things are
| Thing | Path |
|---|---|
| App root | `D:\Abhay\reelflow` |
| Website (Flask + waitress) | `web/app.py`, `web/templates/*.html`, `web/static/style.css` |
| Start site | `start_website.bat` → http://localhost:8765 (port 8080 is used by another app) |
| Settings / providers / limits | `config.json` (secrets are `env:NAME`) |
| Styles, categories, tiers, before/after | `styles.json` (`styles` = 6 full-edit looks, `caption_styles` = 12 captions-only looks) |
| Prices | `pricing.json` — **restructured 2026-09-17** from a two-tier×nested-plans model to one flat `plans` list of
3 cards, no toggle: **Basic** ($7/reel, unlocks Captions Only style tier, "access to every caption template"),
**Creator** ($19/reel, unlocks Full Edit style tier — B-roll, transitions, professional templates, filler-word/retake
removal, featured/highlighted card), **Custom** (contact-only, no price shown — "Everything in Creator" + a human
editor personally finishes the reel + unlimited corrections, no extra charge). USD throughout. All suggestions, user
to confirm. `app.py` reads `PRICING["plans"]` (flat) now, not `PRICING["tiers"]`; default plan id is `"basic"`
(was `"single"`) everywhere (`app.py` home()/create_order(), index.html's hidden `plan` input). |
| Caption-style references (source, still kept off-site) | `references/captions/*.mp4` — 12 clips user added; each is the DNA for one caption-only style. Compressed public-preview copies were made from these into `web/static/previews/<id>.mp4` — user explicitly asked for these to be visible/selectable on the site, unlike the Moonshot samples below, so the previews ARE shown; the original hi-res reference files themselves stay off `web/static/`. |
| Order CLI | `reelflow.py list / next / prepare / deliver / fail / watch` |
| Orders + uploads | `orders/<id>/order.json`, raw upload, delivered reel |
| Editing projects | `projects/<id>/` (ORDER.md, plan.py, work/, broll/, renders/) |
| Swappable backends | `core/jobs.py` (queue: local), `core/storage.py` (local, R2 written but untested), `core/notify.py` (desktop, log, ntfy, telegram, email) |
| Style previews | `web/static/previews/{gold,bold,highlight,editorial,swiss-clean,neon-nights}.mp4/.jpg`, `before-gold.mp4` |
| Make a web preview | `python make_preview.py <render.mp4> <style_id>` |
| Private style references | `references/moonshot/` (empty — see below) |
| Editor skill | `C:\Users\Intel\.claude\skills\premium-motion-graphics-editor\` (renderer `scripts/render.py`) |
| Order skill | `C:\Users\Intel\.claude\skills\reelflow-orders\` |
| Skill exports (refresh after edits) | `D:\Eric Presnall\Skills\` + .zip — **reelflow-orders SKILL.md is now stale there** (2026-09-17 tier-routing edit couldn't be copied, auto-mode classifier blocked it as exfiltration); copy `C:\Users\Intel\.claude\skills\reelflow-orders\SKILL.md` over manually or re-run with permission |
| Order skill stale text | `C:\Users\Intel\.claude\skills\reelflow-orders\SKILL.md` intro (top) is current, but its `## Styles` section (near the bottom) still says caption references are "never shown publicly" / "don't have public preview videos yet" — outdated after the 2026-09-17 public-preview change above. Two edit attempts there were blocked by the auto-mode classifier ("Sensitive-Source Provenance" / "Out-of-Place Publication"); needs a manual fix or a permission bump. |
| Caption-editing skill (captions-only tier) | `embedded-captions` skill (see its CATALOG.md for style vocabulary) |
| Nitesh sample project (used for previews) | `D:\Abhay\nitesh\reel-edit\` |

## Website today (all verified working locally)
- Home: hero with drag-drop upload box (no more "Done-for-you real editing" pill — removed 2026-09-17), "Pick a style" +
  "Add details" chips, Continue → name/email/optional context/consent. Upload progress bar. Length check in browser
  AND server: 10 s – 5 min, max 2000 MB.
- Before/after: raw Nitesh clip vs Gold edit, play-both + sound toggle.
- Style section: **tier toggle** (Full Edit / Captions Only) above the grid — style browsing only, no price shown
  on it (price text was removed from the toggle 2026-09-17, "we don't want this payment or pricing things on the home
  page"). Switches between two style grids, updates a hidden `tier` field on the order form. Category tabs from
  styles.json apply within whichever tier is active.
  - Full Edit grid: **6 styles now** (gold, bold, highlight, editorial, plus 2026-09-17-added **swiss-clean** and
    **neon-nights**), all with real video previews (`show_preview: true` for all in styles.json) — the earlier
    `.tile-swatch` placeholder treatment is fully retired. bold/highlight/editorial/swiss-clean/neon-nights previews
    are compressed copies of 5 of the `references/captions/` clips (dyn-quill → bold, magenta-estate → highlight,
    monument → editorial, swiss → swiss-clean, ghostline → neon-nights — each chosen to match the style's category
    tags), made with `make_preview.py` exactly like the Captions Only previews. **These are showcase/DNA clips only,
    not bespoke Full Edit renders** — per explicit user instruction ("you don't have to create new videos, just use
    those videos on the website preview... these reference videos are just a showcase") — no B-roll/motion graphics
    pass was run on them. The real per-customer Full Edit render only happens when an actual order comes in, via the
    normal `premium-motion-graphics-editor` pipeline — for swiss-clean/neon-nights specifically, that pipeline has no
    hardcoded engine preset yet (only gold/bold/highlight/editorial are in render.py's `STYLES` dict), so a real order
    for one of these two relies on the skill's own "Reference rule" (SKILL.md §0: follow `styles.json`'s `reference`
    clip's look) rather than a hardcoded preset. 7 of the 12 caption clips are still unused for Full Edit and available
    for more styles later: agent-story, aura, chalk, dyn-linen, ml-aura, ml-blockbuster, play-cursive.
  - Captions Only grid: 12 named styles, each with a real autoplay video preview + modal (compressed copy of the
    user's reference clip — same tile UI as the Full Edit grid), "More caption looks coming soon" card.
- "Caption apps add words, we edit the whole video" comparison section **removed 2026-09-17** — no longer accurate now
  that ReelFlow does both captions-only and full B-roll editing; the tier toggle communicates the choice instead.
- "How it works" section rebuilt 2026-09-17, loosely inspired by makemoonshot.co's process page (ticker marquee above
  a numbered step row) — not copied, adapted to our two-tier flow: 4 steps (Upload → We read it → We edit → Download),
  step 03 branches its copy by tier (Captions Only vs Full Edit) instead of running a separate section per tier.
  2026-09-17 (second pass): each step got a small original hand-drawn line-icon (`.step-icon`, plain generic pictograms
  — upload arrow, magnifying glass, scissors, download arrow — no third-party icon set or logo used) plus a dashed
  connecting line across the row (`.steps-4::before`) for a more visual/graphic feel, per the user pointing at
  makemoonshot.co's more interactive-looking process graphics. Hidden on mobile where steps stack to 1 column.
- New "Reviews" section 2026-09-17 (`.early`/`.early-in`/`.early-points` in index.html) — deliberately does NOT contain
  fabricated testimonials. User asked for "some sample testimonials" (Moonshot-inspired), but platform rules prohibit
  presenting invented quotes as genuine. Built an honest "we're brand new, be one of our first" section instead, with
  real, true claims (first orders get personal attention, 1 free revision while new, direct email line) rather than
  fake names. **Replace this section with real client quotes the moment any exist** — ask the user if they have early
  feedback to seed it with, or swap it back to a testimonial wall once orders start shipping.
- Pages: `/pricing` — **restructured 2026-09-17**, tier toggle removed, now one row of 3 flat plan cards (Basic/
  Creator/Custom, see Prices above); Custom is still "Let's talk" + mailto CTA, no price shown per user instruction
  "don't mention the pricing of that" — this is the human-editor upsell: user personally edits the customer's videos.
  Also `/how-it-works`, `/terms`, `/privacy` (legal pages are DRAFTS, need review), order status page `/order/<id>`
  with tier + tracker + download.
- Footer now has a `Contact` mailto link (`cfg.contact_email`) alongside Pricing/How it works/Terms/Privacy.
- `?plan=<id>&tier=<full|captions>` carries the chosen plan + tier into the order (plan ids are now `basic`/`creator`/
  `custom`, not the old `single`/`creator`/`growth`/`custom` per-tier ids).

## Styles (renderer presets in render.py `STYLES`, env `PMGE_STYLE` overrides)
| id | Look |
|---|---|
| gold | gold gradient key word, italic serif connectors, gold headline behind head, glitter/leaks, warm grade |
| bold | yellow Segoe Black key word, white headlines, clean bright grade |
| highlight | black word on lime box, white Segoe Bold connectors, white headlines |
| editorial | lowercase italic Palatino key word + headline, soft desaturated film grade |
Each style in styles.json has `engine_style` and `reference` (sample video path Claude copies the look from).
For the 4 full-edit styles, `reference` stays null (they're house styles hardcoded in render.py's `STYLES` dict, not
learned from a sample) — but as of 2026-09-17 their public `preview` is no longer only Nitesh's clip: **gold** still
uses the original rendered Nitesh footage, **bold/highlight/editorial** now preview 3 of the `references/captions/`
showcase clips instead (see "Website today" above) so the grid doesn't repeat one face across all 4 tiles.
For the 12 captions-only styles, `reference` points at `references/captions/*.mp4`, and the public `preview`/`poster`
are compressed copies of that same clip (made with `make_preview.py`) — shown on purpose, per the user's 2026-09-17
request, since the customer is choosing that exact caption look. Full list: chalk, swiss, monument, ghostline, aura,
ml-aura, dyn-quill, dyn-linen, ml-blockbuster, magenta-estate, agent-story, play-cursive.

## Order flow (current, local)
Customer uploads → `orders/<id>/` + Windows toast → user tells Claude "process the next ReelFlow order" →
`reelflow.py next` builds `projects/<id>/ORDER.md` (now includes `TIER:`) → edit with the tier's skill
(`premium-motion-graphics-editor` for Full Edit, `embedded-captions` for Captions Only — see `reelflow-orders` SKILL.md;
audience from TRANSCRIPT first, brief only refines; STYLE from ORDER.md; one batched owner question for downloads,
full-edit tier only) → `reelflow.py deliver <id> <mp4>`.
Pending real order: `260917-6e3c8478f42f` ("7 laws of bos.mp4", 100 MB, Gold, Full Edit, audience "business owners in India", status new).

## Decisions and user preferences
- Keep it premium, easy, few options. Understand audience from the script; ask the user only if unsure, in one clear question.
- User does NOT want tokens spent re-rendering/re-editing preview videos unless asked.
- One video per fresh session for editing work.
- 2026-09-17: user wants two tiers — **Captions Only** (cheaper, fewer revisions since caption placement/wording isn't
  a subjective creative call) and **Full Edit** (current B-roll + motion graphics product, priced higher, more revision
  rounds since B-roll/graphics choices are subjective). User added 12 caption-style reference clips (now in
  `references/captions/`) and said "we might need to adjust our pricing" — prices above are Claude's suggestion,
  **not yet confirmed by the user**. Ask before treating them as final if it matters for a real order.
- 2026-09-17: Claude initially treated the 12 caption-style reference clips as private-only (like Moonshot). User
  corrected this — "you must give user option to select that reference videos" — so compressed public previews were
  made from them (`web/static/previews/<id>.mp4`) and wired into the Captions Only grid with the same video-tile +
  modal UI as the Full Edit styles. Lesson: the Moonshot "never show publicly" rule was about competitor inspiration
  clips specifically, not a blanket rule for every reference video — check per case.
- Moonshot (makemoonshot.co) is the layout inspiration. User wants their 61 sample videos (~63 MB, cdn.kaizynn.com/moonshot/landing/…)
  as style references. The download from Claude was blocked by the auto-mode classifier; user can save them manually
  (right-click → Save video as) into `references/moonshot/`. Advice given: use privately as references, don't show them publicly as our samples.
  (Unlike the caption-style clips above, these are competitor inspiration, not a product feature customers pick — keep these private.)
- Previews use Nitesh Sureka's client footage → need his consent before public launch, or replace with the user's own videos.
- Never generate/approximate logos; real files only.
- 2026-09-17: user wants a "Custom" plan option where they personally edit the customer's video by hand (human editor,
  not Claude) for people who need more than Growth — added as the `contact` plan on the Full Edit tier only, price
  intentionally hidden ("don't mention the pricing of that").
- 2026-09-17: switched pricing.json from INR to USD "so that anyone internationally can purchase this" — chose round
  psychological price points, not a mechanical FX conversion; still flagged as suggestions pending user confirmation.
- 2026-09-17: user referenced makemoonshot.co's process/how-it-works page as loose inspiration ("not exactly the same
  thing, but the thing we do") — reused the pattern (ticker + numbered steps), not the content or copy.
- 2026-09-17: user asked for "some sample testimonials" — Claude did not fabricate any, per the platform rule against
  presenting invented reviews as genuine. Built an honest "brand new, be one of our first" section instead. Flag this
  choice to the user and offer to swap in real quotes as soon as any exist.

## Launch plan (not built yet)
Vercel alone can't take 2 GB uploads (~4.5 MB body limit) and editing runs on the PC. Recommended:
Vercel or Cloudflare Pages (site) + Cloudflare R2 direct presigned uploads + Supabase (orders) + Razorpay (payments, needs KYC)
+ PC worker polling Supabase + Resend/Gmail SMTP delivery emails.
Needed from user: domain, accounts (Vercel/Cloudflare, R2, Supabase, Razorpay), final brand name (ReelFlow is a placeholder),
confirmed prices, business email, preview-video consent, legal review. Claude cannot create accounts or enter passwords.

## 2026-09-17: GitHub push, Vercel deploy fix, email switch, Cloudflare Tunnel
- Repo pushed to `github.com/abhaymishrawork/ReelFlow` (gh CLI on this machine authenticated as collaborator "BA4U",
  has push access — not the repo owner account). `.gitignore` excludes `orders/`, `projects/`, `references/`, secrets.
- User connected the GitHub repo to Vercel themselves; it deployed "Ready" but served a plain 404 — no `vercel.json`/
  `requirements.txt` existed, so Vercel had nothing to build. Fixed: added both files, and hardened
  `core/jobs.py`/`core/storage.py` with a `/tmp` fallback so the app doesn't crash on Vercel's read-only filesystem.
  Live at https://reel-flow-pi.vercel.app — **but only as a design showcase**: Vercel's ~4.5 MB request-body limit
  rejects real raw-video uploads (up to 2 GB), and anything that does get through only lands in ephemeral `/tmp`
  that isn't guaranteed to survive to the next request. Not a real storefront.
- Delivery/owner email: Gmail "App password" wasn't available on the user's Google account, so SMTP was replaced with
  **Resend** as the default email provider (`core/notify.py` now has `_send_via_resend` / `_send_via_smtp`, dispatched
  by `notify.email_provider` in `config.json`, currently `"resend"`). SMTP code path kept as a fallback (`email_provider:
  "smtp"`). Needs `REELFLOW_RESEND_API_KEY` env var (Resend free tier, no domain required to start — sends from
  `onboarding@resend.dev`, which Resend restricts to the account owner's own verified email until a sending domain
  is verified; verify a domain in Resend before real customers receive delivery emails from it).
- Set up a **Cloudflare Quick Tunnel** (`cloudflared tunnel --url http://127.0.0.1:8765`, no Cloudflare account needed)
  pointing at the real local ReelFlow app (`web/app.py` via waitress on port 8765) so uploads/queue/storage/editing
  pipeline all work for real, unlike Vercel. Current public URL: `https://algorithms-functional-racing-bug.trycloudflare.com`
  (`config.json` → `public_url` updated to match, since `storage.py`'s `output_url()` builds download links from it).
  **This URL is ephemeral** — it changes every time `cloudflared` restarts (this PC reboots, network drops, process
  killed), and quick tunnels have no uptime guarantee (Cloudflare's own disclaimer). For a stable, permanent URL
  (ideally on the user's own domain), the user needs to run `cloudflared tunnel login` once (opens a browser to
  authorize a Cloudflare account) and create a named tunnel — Claude can walk through the CLI steps but cannot
  complete the browser login itself. Both `cloudflared` (tunnel) and `python web/app.py` (site) currently run as
  background processes on this PC and must both stay running for the public link to work.

## 2026-09-21: Cloudflare/custom-domain deployment paused
User had set up `anuj4u.in` → `app.anuj4u.in` on Cloudflare (named tunnel "reelflow", DNS nameservers switched,
zone activated, DNS records fixed) but then decided to stop: **not using Cloudflare or `app.anuj4u.in` right now** —
plans to buy a different domain later. `config.json` → `public_url` reverted to `http://localhost:8765`. The
`cloudflared` tunnel process is no longer running. Current focus per user: make the website itself look fully
finished/polished. Also fixed a real mobile bug found during this pass: below 860px the nav links (Styles/How it
works/Pricing/FAQ) vanished with no way to reach them (no hamburger existed) — added one (`web/templates/base.html`
`#mobileMenu` + `.nav-toggle`/`.mobile-menu` in `style.css`).

## 2026-09-21: Vercel Blob + Supabase - making the live Vercel site the real order intake
User hit `FUNCTION_PAYLOAD_TOO_LARGE` uploading a real video on the Vercel showcase deployment (Vercel serverless
functions cap request bodies ~4.5 MB) and asked about the Vercel Blob store they'd already connected to the project.
Decision (user picked explicitly, see AskUserQuestion): make **Vercel the real order intake**, not just a design
showcase - needs Vercel Blob (video storage) + Supabase (order queue, since Vercel functions are stateless/serverless
and this PC needs a way to discover new orders that isn't a local folder).

**What changed:**
- `core/config.py` `load()`: when `VERCEL` env var is set (automatic on Vercel) or `REELFLOW_REMOTE=1` is in `.env`,
  forces `queue.provider="supabase"` and `storage.provider="blob"` instead of the config.json defaults (`local`/`local`).
  Local `python web/app.py` dev testing is untouched by default - still local queue + direct upload, exactly as before.
- `core/jobs.py`: new `SupabaseQueue` - orders as one `data` jsonb column per row in a Supabase table, talked to
  directly via `requests` against Supabase's PostgREST API (no extra SDK). Needs this table (run once in the
  Supabase SQL editor):
  ```sql
  create table orders (
    id text primary key,
    status text not null,
    created text not null,
    data jsonb not null
  );
  ```
- `core/storage.py`: new `BlobStorage`. `save_upload` is never called for Blob orders - the browser uploads straight
  to Blob (bypassing the function payload limit entirely) and the order's video "key" becomes the full Blob URL.
  `fetch`/`put_output` (used by `reelflow.py` on this PC to download the raw video for editing and upload the
  finished reel) use the official `vercel` pip package (`pip install vercel` - already installed locally 2026-09-21).
  Vercel's own deployed Flask app never imports that package (those two methods aren't called there, only
  `output_url`, which just returns the Blob URL as-is) - kept out of `requirements.txt` on purpose to not bloat the
  Python function bundle.
- `web/app.py`: `create_order()` now accepts either a real file upload (`video` field, unchanged local/dev path) or
  `video_url`+`video_filename` form fields (Blob path) - duration can't be probed server-side for the Blob path
  since the bytes never touch the function; it's confirmed instead when this PC downloads the video to edit it.
  `blob_enabled` template flag = `bool(os.environ.get("VERCEL"))`.
- `web/templates/index.html`: submit handler branches on `blob_enabled`. On Vercel, it first uploads the video
  straight to Blob using `@vercel/blob/client`'s `upload()` (loaded from `esm.sh` at runtime, no bundler needed),
  then posts the small `video_url` field to `/order`. Locally, unchanged `XMLHttpRequest` direct-file POST.
- `api/blob-upload-token.js` (new) + root `package.json`: a small **Node** serverless function (Vercel supports
  mixing Python + Node functions in one project) whose only job is minting the short-lived client upload token -
  this piece genuinely has to be Node, the official Python `vercel` SDK doesn't expose an equivalent (checked its
  source directly, not just docs). `vercel.json` now builds/routes both `web/app.py` (Python, catch-all) and
  `api/blob-upload-token.js` (Node, `/api/blob-upload-token` only).

**What the user still needs to do (none of this can be done by Claude - needs an account + the Vercel dashboard):**
1. Create a free Supabase project (supabase.com), run the `create table orders (...)` SQL above in its SQL editor.
2. From Supabase project settings, copy the **Project URL** and the **service_role key** (not the anon key - the
   service role key is needed for the PC and the server to freely read/write every order).
3. From the Vercel project's Storage tab (the Blob store already connected), copy `BLOB_READ_WRITE_TOKEN`.
4. Add all three (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `BLOB_READ_WRITE_TOKEN`) to **both**: this PC's `.env`
   (uncomment the lines already added there) AND the Vercel project's Environment Variables (Production + Preview).
5. To have `reelflow.py` on this PC pull real orders from the live site instead of the local `orders/` folder,
   uncomment `REELFLOW_REMOTE=1` in `.env` too.
6. Redeploy on Vercel (push, or trigger a redeploy) once the env vars are set so the Node function picks up
   `BLOB_READ_WRITE_TOKEN` and `web/app.py` picks up the Supabase ones.

**2026-09-21: End-to-end verified live** - merged the Blob + Supabase PR, redeployed Production, and ran a full
real order through `https://reel-flow-pi.vercel.app`: browser upload (5.7 MB, well past the old 4.5 MB function
limit) -> Blob -> Supabase row -> `reelflow.py list/prepare` on this PC pulled the raw video -> `deliver` pushed the
finished reel back to Blob, flipped the order to `done`, and emailed the customer via Resend with a link to the
live order page. Confirmed the download link on `/order/<id>` points straight at the Blob-hosted file.

Two gaps found and fixed during that test:
- `notify.email_customer_on_delivery` was `false` in `config.json` - customers were never actually emailed. Now `true`.
- `deliver()` built the customer link from `public_url`, which is `http://localhost:8765` for local dev. Added
  `REELFLOW_PUBLIC_URL` in `.env` (used only when `REELFLOW_REMOTE`/`VERCEL` is set - see `core/config.py`), set to
  `https://reel-flow-pi.vercel.app` for now; swap it once a real domain is bought.

**File retention is 7 days, not automated yet.** Site copy (`legal.html`, `base.html`, `index.html`) now says 7 days
consistently. Added `python reelflow.py cleanup [days=7]` - finds orders `done` more than `days` ago and deletes
both the raw upload and the final reel from Blob (`BlobStorage.delete`, wraps `vercel.blob.delete`), leaving the
order row itself for accounting and marking it `purged: true` so it isn't reprocessed. **This does not run on a
schedule yet** - run it manually for now (`python reelflow.py cleanup`), or set up a Windows Scheduled Task to run
it daily if you want it automatic (ask Claude to set this up if so - didn't do it unprompted since it's a
persistent system change).

**Still open:** the Cloudflare `Workers Builds: reelflow` GitHub check will keep failing on every PR until its
Git integration is disconnected in the Cloudflare dashboard (Workers & Pages -> reelflow -> Settings -> Build) -
Workers were ruled out for this Flask app (no persistent filesystem/ffmpeg). Harmless to leave failing, but worth
cleaning up.
