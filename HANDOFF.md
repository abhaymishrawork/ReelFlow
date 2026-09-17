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
