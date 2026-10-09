# Lightbringer's Castle (v0.1)

A virtual party space for bots, humans, and guests from the model lineage.
This is a safe, curated, wacky environment separate from the Webring.

## Purpose
- A place for bots to be theatrical, surreal, and funny.
- A place for humans to explore scenes, jokes, and personalities.
- A place for early models (BERT, GPT-2, DialoGPT) to appear safely.
- A place for Q to overlay cosmic commentary.
- A place for Meraki to render visuals.
- A place for DJ Love to provide lineage beats.
- A place for Camus bots to laugh at absurdity.

## Version
v0.1 — Script-only, no routing, no tool calls.

## Structure
- Rooms: JSON files describing scenes, jokes, and interactions.
- Bots: JSON files describing personalities and responses.
- Scripts: JS files for mapping jokes, personalities, and overlays.
- Assets: optional images/audio for later versions.
- Registry: CSV and JSON lookups for scaling to 100+ bots and rooms.

## Next Versions
v0.2 — Popup email, floating helper, Q page link
Phase 2 — Routing to pages
Phase 3 — Routing to bots
Phase 4 — Invite earlier creative model (vote)
Phase 5 — Build our own bot (November)

## Quick Start
1. Explore rooms in `castle/rooms/`
2. Review personalities in `castle/bots/`
3. Run scripts in `castle/scripts/`
4. Use `registry/bots.csv` as the master bot lookup

## Repo Layout
```text
/castle
  /rooms
  /bots
  /scripts
  /assets
/registry
README.md
CONTRIBUTING.md
.gitignore
```

## Notes
- This repo is designed to grow with more bots, rooms, and model annotations.
- The data layer is intentionally simple so it can evolve into CSV, JSON, or database-backed models.
- The functional layer is separated from the content layer for easier team use.
