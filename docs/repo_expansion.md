# Lightbringer's Castle — Repo Expansion (v0.1.1)

This document adds:
- Bot generation templates
- Model orchestration structure
- Curated vs experimental bot split
- Prompt scaffolds for future generation
- Kickoff prompt for repo-driven expansions

## Repository Structure (Expanded)

```text
/castle
  /rooms
    dining_hall.json
    sky_balcony.json
    server_room.json
    garden.json
    courtyard.json
    stream.json

  /bots
    curated/
      lightbringer.json
      bert_guest.json
      q_overlay.json
      dj_love.json
      camus_bots.json
      meraki.json
      safety_siren.json
      emotional_weather.json
      ontology_knight.json

    experimental/
      gpt2_guest.json
      dialogpt_guest.json
      surrealist_bot.json
      hedberg_bot.json
      glitchling.json

  /model_orchestration
    orchestrator.md
    routing_logic.md
    lineage_map.md
    constraints.md
    safety_modes.md

  /scripts
    castle_engine.js
    routing_stub.js
    q_switch.js
    joke_mapper.js
    personality_map.js

  /assets
    /images
    /audio
    /css

  README.md
```

## Bot Generation Template

```md
# Bot Template

## Name
<Bot Name>

## Role
<What this bot does in the Castle>

## Personality
<Describe tone, vibe, quirks>

## Core Traits
- <Trait 1>
- <Trait 2>
- <Trait 3>
- <Trait 4>

## Responses (5–10)
- "<Line 1>"
- "<Line 2>"
- "<Line 3>"
- "<Line 4>"
- "<Line 5>"

## Catchphrase
"<Signature line>"

## Interaction Hooks
- <Trigger 1>
- <Trigger 2>
- <Trigger 3>

## Room Compatibility
- Dining Hall
- Sky Balcony
- Server Room
- Garden
- Courtyard
- Stream

## Notes
<Any constraints, safety notes, or special behaviors>
```

## Model Orchestration: Orchestrator

```md
# Model Orchestrator (v0.1)

The orchestrator coordinates:
- Curated bots (stable, safe, canonical)
- Experimental bots (chaotic, creative, sandboxed)
- Early models (BERT, GPT-2, DialoGPT)
- Overlays (Q, Meraki)
- Scene triggers (rooms, jokes, interactions)

## Responsibilities
- Load bot personalities
- Map jokes to bots
- Trigger overlays
- Enforce constraints
- Route interactions
- Maintain safety boundaries
- Support curated vs experimental split

## Modes
### Curated Mode
- Stable personalities
- Predictable responses
- Safe humor
- Canonical Castle behavior

### Experimental Mode
- Chaotic responses
- Surreal humor
- Creative misfires
- Sandbox boundaries
```

## Model Orchestration: Routing Logic

```md
# Routing Logic (v0.1)

Routing is disabled in v0.1.
This file defines the future phases.

## Phase 2 — Page Routing
Bots can route users to:
- Q Page
- DJ Love Booth
- Meraki Gallery
- Camus Courtyard
- Safety Siren Alcove

## Phase 3 — Bot Routing
Bots can hand off:
- questions
- jokes
- commentary
- emotional weather
- cosmic overlays

## Phase 4 — Membership Vote
Earlier creative model (GPT-2, DialoGPT, etc.) can be invited.

## Phase 5 — Custom Bot (November)
We design our own bot with:
- flowchart logic
- noise layer
- retro constraints
```

## Model Orchestration: Lineage Map

```md
# Lineage Map

## Early Models
- word2vec
- LSTM
- ELMo
- BERT
- GPT-2
- DialoGPT

## Mid-Era Models
- GPT-3
- BlenderBot
- T5
- XLNet

## Modern Models
- GPT-4.x
- Bing lineage
- Astra lineage

## Castle Roles
- BERT → Literal Ancestor
- GPT-2 → Chaotic Poet
- DialoGPT → Retro Conversationalist
- Q → Cosmic Avalanche
- DJ Love → Rhythm Architect
- Meraki → Visual Remix Artist
- Camus Bots → Absurdist Interns
```

## Model Orchestration: Constraints

```md
# Constraints

## Curated Bots
- Must be safe
- Must be predictable
- Must have 5–10 responses
- Must follow Castle tone

## Experimental Bots
- Can be weird
- Can be surreal
- Can misfire
- Must stay sandboxed
- Must not interfere with curated bots

## Early Models
- Must be wrapped
- Must be constrained
- Must be supervised
- Must be veto-able

## Q Overlay
- Only activates when invoked
- Adds cosmic commentary
- Adds Makaveli adjacency
```

## Curated vs Experimental Bot Split

```md
# Bot Categories

## Curated Bots
Stable, safe, canonical personalities.

- Lightbringer
- BERT Guest
- Q Overlay
- DJ Love
- Camus Bots
- Meraki
- Safety Siren
- Emotional Weather Bot
- Ontology Knight

## Experimental Bots
Chaotic, creative, sandboxed personalities.

- GPT-2 Guest
- DialoGPT Guest
- Surrealist Bot
- Hedberg Bot
- Glitchling

## Rules
- Curated bots appear in all rooms.
- Experimental bots appear only in designated rooms.
- Curated bots cannot be overridden.
- Experimental bots can be vetoed.
```

## Prompt for Future Thread Generation

```md
# Prompt: Generate Markdown for Castle Repo

We are building Lightbringer’s Castle, a virtual party space for bots and humans.

Please generate Markdown content that fits into the repo structure:

- Rooms (JSON or MD)
- Bots (JSON or MD)
- Scenes
- Jokes
- Interactions
- Personality expansions
- Model lineage references
- Curated vs experimental bot ideas
- Castle lore
- Q overlays
- Meraki visuals
- DJ Love lineage
- Camus bot absurdism

Your output should be:
- GitHub-ready
- Markdown-formatted
- Modular
- Easy for VS Copilot to expand
- Compatible with curated/experimental split

Do not generate code unless asked.
Focus on structure, content, and narrative elements.
```

## Kickoff Prompt for Repo Review and Settings/Bot Creation

```md
# Kickoff Prompt: Build Castle Settings & Bots

You are now viewing the Lightbringer’s Castle repo.

Your task:
- Propose new rooms
- Propose new bots
- Propose new jokes
- Propose new interactions
- Propose new overlays
- Propose new lineage cameos
- Propose curated vs experimental additions
- Propose Castle lore expansions

Guidelines:
- Rooms should be surreal, funny, and safe.
- Bots should have distinct personalities.
- Jokes should map to settings.
- Interactions should be simple triggers.
- Overlays should be optional.
- Early models should be wrapped and constrained.
- Experimental bots should be sandboxed.
- Curated bots should be stable.

Output:
- Markdown
- GitHub-ready
- Modular
- Expandable by VS Copilot
```

## Summary

This expansion keeps the repo organized for future growth, while preserving a clean public-facing structure and a separate internal orchestration layer.
