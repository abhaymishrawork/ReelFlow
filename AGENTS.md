# Instructions for AI agents

Read `README.md` -> "Process an order" before doing anything with orders or videos.

- Orders come from the live site through Supabase. Run `python reelflow.py list new` to see them.
- `projects/<order_id>/ORDER.md` is the brief for one order. `skills/<style id>/README.md` explains the style.
- Tier `full` uses the `premium-motion-graphics-editor` skill. Tier `captions` uses the `embedded-captions` skill.
- Never commit `.env`, never print its values, never contact customers directly.
- Deliver only with `python reelflow.py deliver <order_id> <file>`.
- Project history and decisions: `HANDOFF.md`.
