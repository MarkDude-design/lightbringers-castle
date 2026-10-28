---
title: Castle thread miscellany — October 2026
status: archive
type: conversation-digest
owners: [Mark, Meraki, Z]
last_reviewed: 2026-10-28
tags:
  - archive
  - puppy
  - fedora
  - workflow
  - openrouter
  - mcp
  - observability
  - cost-control
---

# Castle thread miscellany — October 2026

This digest holds useful project residue recovered while extracting talk
material. It is not an implementation plan, spending authorization, or current
security specification. Current repository code and merged documentation win
when they disagree with this archive.

## Minimal Linux proof-of-concept residue

Provenance: Mark/Shared. Status: parked design direction.

- Start from the brilliance of Puppy’s live, layered design rather than treating
  every historical Puppy component as mandatory.
- Minimal boot plus CLI is the first useful body. GUI is secondary.
- An SFS/squashfs-style module layer remains attractive because features can be
  added, removed, and compared without rebuilding the entire conceptual system.
- Select one of Mark’s available laptops based on Linux compatibility, then pin
  the proof of concept to that hardware. Hardware choice comes before generic
  driver ambition.
- Wi-Fi ugliness is acceptable during development, although the chamber’s final
  clean configuration has no network.
- Early size intuition: kick roughly 20 MB around experimentally; expect a
  practical text-first build to grow into roughly 40–60 MB and remain under
  100 MB. These are design guesses, not measured artifacts.
- A simple terminal reader/editor is sufficient for early human inspection.
- Treat 0.9 as a learning build. A clean 1.0 or “Puppy 2.0 Fedora” rewrite may
  be cheaper than preserving accidental legacy.
- Puplet/remaster and module approaches may coexist if the combination does not
  enlarge the attack surface without a measured benefit.

Promotion trigger: a measured boot/HELLO build receipt on selected hardware or
in the P0a workflow.

Related current material: `docs/workflow/` and draft PR #7 history.

## Team communication and model-loop residue

Provenance: Mark/Shared. Status: active principle, implementation incomplete.

Primary goal: remove two or three conversational exchanges from each bounded
task. Real-time model conversation is optional; a reliable digest answering
20-plus queued questions can create most of the value.

Desired minimum:

1. Host sends a bounded packet.
2. A model can say Hello World and return an unambiguous ACK.
3. A worker can answer a batch of questions.
4. Another model or Z can review in parallel.
5. Failure with one or two models can route to another named model.
6. Every carry preserves task identity, constraints, provenance, token/cost
   observations, and STOP behavior.

The smallest success is communication that saves steps. It is not a complete
orchestration feature set.

Related current material: draft PR #6 history and
`castle/project_tasks.py`. Do not copy PR #6 schemas here.

## Roles recovered from the thread

These are historical working assignments, not permanent access control:

| Seat | Working purpose |
| --- | --- |
| Mark | Owner, spend authority, human acceptance, and merge gate except where repository policy explicitly delegates |
| Meraki | Architecture synthesis, final technical review, and cross-thread continuity |
| Z | Coordinator/reviewer, spec compression, parallel Puppy/space lane, and temporary Mistral control period |
| Codex | Bounded repository implementation, tests, receipts, and PR handback |
| Cheaper/OpenRouter models | Mechanical reads, batch questions, first-pass classification, and replaceable worker lanes |
| Long-context model | Import and parse large Markdown/thread exports without making final policy |

Important later clarification already present in repository governance: a
Mistral model used as a module is not automatically the Z seat.

## MCP/tool inventory routing

The conversation produced a large raw inventory. Route it instead of
duplicating it:

- Boundary tools: scrubber gate, recorder, ACK register, token ledger, register
  watch, crib watchdog, canary flip, inversion, run differ, manifest registry,
  and offline verifier.
- Team-flow tools: thread scanner, packet ferry, bounded search party, and lunch
  receipt.
- Fun tools: lossy Dante/IdiotBot relay and register-face renderer.

Current disposition:

- The OpenRouter/MCP team bus and ACK qualification are represented by draft
  PR #6.
- The local room-tool loop and project-task runner on `main` are narrower,
  already implemented stepping stones.
- Do not build all inventory items merely because they have names.
- Next tools should close an observed workflow gap or produce an acceptance
  receipt unavailable through existing code.

## Cost and routing residue

Provenance: Mark/Z/Meraki. Status: partly adopted.

- Unit-price lanes and per-task budgets solve different problems.
- Cost per accepted result is more meaningful than price per token.
- Pricing observations must be dated; model-name allowlists rot.
- A free router is useful for exploration but weak evidence for stable model
  identity.
- Model fallback should be explicit and receipted, not silent.
- Langfuse was identified as a possible future trace/spend spine; it is not an
  adopted dependency here.
- Do not create a second price lane until a real rejected task demonstrates the
  need.

Current implementation: `castle/project_tasks.py` and
`castle/PROJECT_TASKS.md`.

## Repository/workflow preferences

Provenance: Mark. Status: keeper.

- Lost merges are a higher concern than a merely imperfect push.
- Code comments and provenance should make work traceable to another person.
- Models may assist with commits, but human acceptance remains distinct from
  model review.
- Build something bounded, learn from it, and rewrite when the evidence favors
  replacement over legacy repair.
- Keep pull requests scoped so a reviewer can tell whether a change is code,
  content, evidence, workflow, or policy.
- Preserve failed attempts and costs; unsuccessful does not mean free.

## Visual residue not yet assigned to a talk

- Iterate many bot designs cheaply, then print several per page for comparison.
- Use simple android heads, googly eyes, fixed brows, and mustaches as the common
  visual grammar.
- Explore sticker and stencil versions where permitted.
- Strange one-off designs can still expose a useful direction; do not confuse
  visual failure with zero information.
- Keep celebrity resemblance generic and archetypal unless rights and intent
  are explicit.
- The “shit happens” tone fits better than hostile or vandalism-coded imagery.

Promotion trigger: a chosen five-character live-demo cast and a versioned
display map.

## Unresolved forks worth retaining

- Puppy-first proof of concept versus Fedora-first integration.
- USB hash-chain recorder versus an optical-media demonstration variant.
- When, if ever, a remote model belongs near a chamber whose primary rule is no
  network.
- Whether register monitoring remains deterministic-only or gains a bounded
  classifier sensor.
- Per-role price lanes versus one task-wide lane.
- UTC policy dates versus a recorded, explicit policy timezone.
- Whether a first public artifact is a talk, a tiny boot image, a web experiment,
  or a combined demonstration.

## Archive hygiene

When one of these items becomes real:

1. link the implementing PR or specification here;
2. change its status to promoted or superseded;
3. avoid copying the same paragraph into another archive;
4. preserve the original provenance and uncertainty.
