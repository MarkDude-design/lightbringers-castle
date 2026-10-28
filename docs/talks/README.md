---
title: Castle talk workspace
status: active-index
type: index
owners: [Mark, Meraki]
last_reviewed: 2026-10-28
tags: [talks, archive, fragments, routing]
---

# Castle talk workspace

This directory holds material that can become a talk, demo, slide, workshop, or
public explanation. It is intentionally upstream of a finished script.

## Files

| File | Purpose | Current status |
| --- | --- | --- |
| [CHAMBER_FRAGMENT_BANK.md](CHAMBER_FRAGMENT_BANK.md) | Keeper lines, demo beats, possible talk spines, and safety framing recovered from the Castle design thread | Seed bank |
| [../archive/CASTLE_THREAD_MISCELLANY_2026-10.md](../archive/CASTLE_THREAD_MISCELLANY_2026-10.md) | Useful residue that is not presently talk material or an adopted specification | Archived, searchable |

## Minimal metadata

New talk notes should begin with YAML front matter using these fields:

- `title`
- `status`
- `type`
- `owners`
- `last_reviewed`
- `tags`

Allowed working statuses:

| Status | Meaning |
| --- | --- |
| `seed` | A useful fragment with no chosen home |
| `keeper` | Preserve wording or idea; likely reusable |
| `draft` | Assigned to a particular talk or demo |
| `needs-verification` | Public claim requires sourcing before use |
| `parked` | Deliberately deferred, not discarded |
| `archive` | Context or provenance; not current direction |
| `superseded` | Retained only to explain an older decision |

## Core tags

Use a small vocabulary and combine tags instead of inventing near-synonyms:

- Subject: `ai-safety`, `containment`, `observability`, `logic-gates`,
  `open-source`, `workflow`, `cost-control`, `puppy`, `fedora`.
- Form: `line`, `story`, `demo`, `visual`, `joke`, `workshop`,
  `audience-question`.
- Readiness: `talk-ready`, `needs-verification`, `needs-design`,
  `needs-code`.
- Audience: `general`, `technical`, `security`, `fedora`, `learners`.

## Provenance labels

- **Mark** — originated by Mark in the working conversation.
- **Meraki** — originated by Meraki.
- **Z** — originated by Z/Mistral.
- **Shared** — materially co-developed; splitting the sentence would misstate it.
- **Established** — known external pattern reused by the project.

A provenance label preserves credit. It is not a claim that the wording is a
verbatim transcript. Exact quotations must be marked **verbatim candidate** and
checked against the source conversation before public use.

## Routing rule

Promote material by moving or linking it; do not silently duplicate it.

- Finished talk scripts belong in a future `docs/talks/scripts/`.
- Slide-specific notes belong beside the script they support.
- Machine contracts belong in `specs/`, not here.
- Test evidence and provider observations belong in `docs/evidence/`.
- Unresolved but useful residue belongs in `docs/archive/`.
