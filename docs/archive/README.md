---
title: Castle archive
status: active-index
type: archive-policy
owners: [Mark, Meraki]
last_reviewed: 2026-10-28
tags: [archive, provenance, routing]
---

# Castle archive

This directory preserves useful residue from design conversations when it does
not yet belong in code, a specification, a registry, or a finished talk.

Archive means **recoverable context**, not adopted policy.

## Put material here when

- it may matter later but has no current implementation owner;
- it explains why an option was considered, deferred, or rejected;
- it is a build estimate, workflow preference, visual idea, or unresolved fork;
- promoting it into a live specification would overstate its maturity.

## Do not put material here when

- it is current machine behavior: document that beside the code;
- it is test or provider evidence: use `docs/evidence/`;
- it is an adopted contract: use `specs/`;
- it is a current bot or room: use the registries and Castle JSON;
- it contains credentials, private transcripts, medical/personnel material, or
  unpublished third-party information.

## Archive entry format

Each entry should record:

- source period;
- provenance;
- status;
- tags;
- what would cause promotion;
- links to any current implementation or superseding decision.

Prefer one curated digest over raw conversation pasta. Preserve exact wording
only when the wording itself matters, and label it for source verification.
