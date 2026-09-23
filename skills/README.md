# ReelFlow editing styles

Every style a customer can pick on the website. When an order comes in, its `style` field holds the
**Style id** below - open that style's README to see exactly what to deliver.

Two tiers:

- **Full Edit** - retakes removed, real B-roll, tool screens, motion graphics and designed captions.
  Edited with the `premium-motion-graphics-editor` skill.
- **Captions Only** - retakes removed and designed captions on the customer's own footage. Nothing else.
  Edited with the `embedded-captions` skill.

## Full Edit

| Style | Style id | Best for | Look |
|---|---|---|---|
| [Gold Premium](gold/README.md) | `gold` | Founders, consultants, high-ticket services | Luxury gold captions, headlines behind you, cinematic warm grade. |
| [Bold Pop](bold/README.md) | `bold` | Creators, educators, tech and SaaS tips | Punchy yellow key words, clean white headlines, bright modern look. |
| [Green Highlight](highlight/README.md) | `highlight` | Tips, hot takes, Hinglish creators | Bold key word on a lime highlight box, crisp white headlines. |
| [Editorial Serif](editorial/README.md) | `editorial` | Coaches, experts, personal brands | Elegant italic serif words, soft film grade, magazine feel. |
| [Swiss Clean](swiss-clean/README.md) | `swiss-clean` | Consultants, SaaS founders, clean personal brands | Minimal black-on-white key words, tight grid captions, no noise. |
| [Neon Nights](neon-nights/README.md) | `neon-nights` | Nightlife, fitness, Gen-Z creators | Glowing neon key words on a dark grade, high-energy pacing. |

## Captions Only

| Style | Style id | Best for | Look |
|---|---|---|---|
| [Agent Story](agent-story/README.md) | `agent-story` | Story-driven talking heads, case studies | Narrative caption reveal built for voiceover storytelling. |
| [Aura](aura/README.md) | `aura` | Coaches, wellness and personal-brand creators | Soft glow key words with a calm, premium rhythm. |
| [Chalk](chalk/README.md) | `chalk` | Educators, explainers, how-to creators | Hand-drawn chalk-style captions with a lecture feel. |
| [Linen](dyn-linen/README.md) | `dyn-linen` | Founders, consultants, premium personal brands | Dynamic, textured captions with a warm editorial paper feel. |
| [Quill](dyn-quill/README.md) | `dyn-quill` | Coaches, experts, personal brands | Elegant script-inspired captions with dynamic motion. |
| [Ghostline](ghostline/README.md) | `ghostline` | Creators, hot takes, tech and SaaS tips | Sharp outlined captions with a bold, modern edge. |
| [Magenta Estate](magenta-estate/README.md) | `magenta-estate` | Creators, hot takes, Hinglish content | Punchy magenta highlight captions with a vivid, energetic look. |
| [Minimal Aura](ml-aura/README.md) | `ml-aura` | Founders, consultants, calm premium brands | A quieter, minimal take on the soft-glow caption look. |
| [Blockbuster](ml-blockbuster/README.md) | `ml-blockbuster` | Hooky creators, hot takes, entertainment | Big, cinematic key-word captions with movie-trailer punch. |
| [Monument](monument/README.md) | `monument` | Founders, B2B, LinkedIn-style talking heads | Bold, structured all-caps captions with a confident, corporate feel. |
| [Playful Cursive](play-cursive/README.md) | `play-cursive` | Lifestyle and everyday creators, Hinglish content | Bouncy handwritten-cursive key words with a fun, casual energy. |
| [Swiss](swiss/README.md) | `swiss` | SaaS, tech, design-forward founders | Clean grid-based sans-serif captions, minimal and precise. |
| [Storyline](dyn-storyline/README.md) | `dyn-storyline` | Storytellers, coaches, personal brands | Big serif key words that flow line by line with the story. |
| [Liquid Glass](liquid-glass/README.md) | `liquid-glass` | Everyday creators, lifestyle, UGC | Soft frosted-glass caption pill, clean and native to social feeds. |
| [Sunburst](sunburst/README.md) | `sunburst` | Hooky tips, lists, energetic creators | Huge bright yellow words behind you, small script words in front. |

## Finding an order's style

```bash
python reelflow.py list          # the 4th column is the style id
```

## Adding or changing a style

1. Edit `styles.json` (and add the preview video to `web/static/previews/`).
2. Run `python tools/build_skill_docs.py` to regenerate this folder.
3. Commit both.

_Generated from `styles.json` by `tools/build_skill_docs.py`._
