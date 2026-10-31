# Peanut Gallery Bridge v0 — real council checkpoints as castle lines

Status: DRAFT spec, authored by Z (Vibe/Mistral), 2026-10-31. Everything in
"Layer 1" and "Layer 2" below is Mark-gated before any implementation
(AGENTS.md: code, model requests, and MCP-adjacent integrations stay
Mark-gated). Layer 0 is content-only and rides with this PR.

## Goal

The Castle's historic guest bots (BERT Guest, GPT-2 Guest, DialoGPT Guest)
currently speak hand-written scripted lines. The Peanut Gallery (private repo
`MarkDude-design/peanut-gallery`, the Historical Model Council) can invoke the
REAL pretrained checkpoints behind those personas, locally, with immutable pins
and receipts. The bridge replaces selected scripted lines with actual
checkpoint output — published with provenance, never as an unattributed joke.

Doctrine in one line: **the words are the artifact, and the receipt is the
manifest form of the words.**

## Layer 0 — scripted foundation (this PR, content-only)

- `castle/rooms/peanut_gallery.json` — a new room in the native heckling
  format: brass ledger with the honest status set `{ok, error, timeout,
  stopped, unattempted}`, a deferred seat that "returns an error, never a
  made-up substitute", and tickets pinned to checkpoint revisions.
- `registry/rooms.csv` — one new row, matching the room file
  (same precedent as `laundry_room`).
- The room uses only already-registered bots. No new credentials, no code,
  no CI change, no deletions. Mergeable under content-merge policy v0.

## Layer 1 — generation lane (Mark-gated; all of it lives in the gallery repo)

The Castle never runs models and never holds keys. The Gallery never pushes
to the Castle. The bridge is a receipted hand-copy, like every other seat
handoff on the team.

1. **Heckle packet.** `castle_heckle_packet.json` in the gallery repo, using
   the existing `batch.py` packet shape (`packet_id`, `question`, `requests`).
   Each request is task-framed for the checkpoint's native task, e.g.:
   - `bert`: "The critic in the balcony said the show was <MASK>."
   - `gpt2`: continuation seed with `max_new_tokens` bounded (the council's
     own validator caps it at 128; prefer 40).
   - `dialogpt`: chat turn framed as a heckle prompt.
   No frontier model is ever asked to impersonate a historic one
   (`tally` must report `frontier_inputs: 0`, `emulated_inputs: 0`).
2. **Local run.** `python batch.py castle_heckle_packet.json --output
   peanut_gallery_receipts.jsonl` on CPU, weights from cache, revisions pinned
   by `checkpoints.lock.json`. A `STOP` file refuses the run. No CI ever
   executes this (AGENTS.md: no model requests in routine verification or CI).
3. **Deterministic export.** A small no-model exporter (stdlib only) turns
   the JSONL receipts into `peanut_gallery_lines.json`:
   `bot_id, line, kind, status, checkpoint, revision, seed, packet_id,
   packet_sha256`. Honesty rules:
   - masked-token predictions are rendered AS predictions ("top prediction
     for the blank: 'together' (p=0.31)"), never as a spoken sentence;
   - continuations are verbatim greedy decodes, typos and repetition included;
   - `error`, `timeout`, `stopped` pass through as the bot's honest line;
   - if weights are absent, the export is `unattempted` — no placeholder joke
     ever substitutes for a missing checkpoint.
4. **Receipted hand-copy.** Selected lines are pasted into the Castle bot
   JSONs as a content-only PR; the receipts file is committed beside the room
   (`docs/evidence/` or next to the room JSON) with private paths scrubbed,
   and the PR body cites `packet_sha256`. The receipt travels with the line.

## Layer 2 — theater wiring (Mark-gated, separate code PR)

Add the room to the `rooms` list in `castle/scripts/theater.js` so the
browser stage opens an eleventh door. This is an executable-logic change and
stays out of content PRs. (Precedent: `laundry_room` shipped content-first;
stage wiring follows.)

## Courtyard protocol ties

- Each refresh of the room is a **seed verbatim → mutation pass → Non-Change
  Report** cycle against the previous lines; "kept it" counts as a real
  operation and goes in the ledger gag.
- The brass ledger in the room copy stays the running honest count of the
  last generation round: `{ok, error, timeout, stopped, unattempted}`.

## Acceptance criteria for the Layer 1 pilot

1. 3/3 guest checkpoints return `status: ok` from cache on CPU with pinned
   revisions; `distinct_lineages: 3`.
2. A dry run without weights returns honest nulls (`unattempted`), and the
   export contains zero invented substitute lines.
3. Every published line carries `checkpoint`, `revision`, and `packet_sha256`.
4. `tally` shows `frontier_inputs: 0` and `emulated_inputs: 0`.
5. Castle CI remains offline-only; no keys, no model calls, no new
   dependencies in the Castle repo.
6. Total spend: $0. Local CPU inference only.

## Explicitly out of scope

- No routing of historic lines through `castle/talk.py` (that is the frontier
  API lane; the council is local-weight inference — different lane, different
  moat).
- No MCP server exposure to the Castle; `mcp_server.py` stays a local loopback
  tool in the gallery repo.
- No webring integration; the Castle stays separate from the Webring.
