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
v0.1 content remains scripted. An experimental live API conversation runner is now available.

## Step into the scripted theater

The [browser stage](castle/theater.html) opens six rooms from the existing
Castle scripts. Cue a character, reveal a punchline, nudge the scenery, or let
Q interrupt. All dialogue is stored content; no model calls or keys are needed.
See [preview instructions and boundaries](castle/THEATER.md). This stage is
separate from the API runners below.

## Talk to real models now

With Python 3.10+ installed, run `python castle/talk.py --interactive`
(or `py -3 castle/talk.py --interactive` on Windows). Enter your Groq and
OpenRouter API keys in the hidden terminal prompts. No dependency installation
or hosting is required. The models take turns, see each other's replies, and
accept your next host message. Read [castle/TALK.md](castle/TALK.md) for details.

The API runner is separate from the scripted personas and runtime probe.
It also has an opt-in OpenRouter `read_room` tool that returns actual room JSON
through a bounded, read-only client-side tool loop. The exact one-command test
and receipt format are documented in [castle/TALK.md](castle/TALK.md).

For a separate, bounded worker/reviewer proposal workflow, see
[Budgeted Project Tasks v0](castle/PROJECT_TASKS.md). It supports an offline
dry run, frozen source packets, cost receipts, and human acceptance without
applying model-generated changes.

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

