# Castle agent workflow

- Read this file and CONTRIBUTING.md. Inspect current main and open PRs before
  changing scope; preserve newer work and do not duplicate another PR.
- Agents own routine checkout, isolated branches, implementation, offline
  verification, bounded repairs, commits, push, and a reviewable draft PR within
  the user's authorization. Do not send Mark terminal chores you can perform.
- Use the existing isolated checkout. Do not create worktrees unless requested.
- Run `python scripts/verify.py` after staging intended new files. Read its
  summary and failed logs; repair causes, never weaken assertions or skip checks.
- Keep model requests, API credentials, pricing refresh, live acceptance,
  deployment, and account changes out of routine verification and CI. Synthetic
  pricing fixtures must be clearly labeled; never refresh real dates for green CI.
- Preserve task IDs, case aliases, ledgers, known/unknown costs, failures, human
  decisions, and unresolved attempts. Never clear evidence or retry uncertain work
  to make a check pass. Keep private runs/transcripts out of Git and CI artifacts.
- Mark owns human artifact acceptance. Merge authority is tiered
  (content-merge policy v0, agreed Mark and Z, 2026-10-21):
  - Z (Vibe/Mistral) may merge without further human approval when the diff is
    content-only: rooms, bots, jokes, docs wording, and registry additions; no
    executable-logic changes, no CI/workflow changes, no credentials or secrets,
    no task/ledger/accounting mutation, and no deletions (repairing a malformed
    registry row with a PR note is allowed). CI verification must be green on
    the PR, and the merge message records "merged under content-merge policy v0".
  - Everything else stays Mark-gated: code, CI, security, credentials,
    deployment, task accounting, model requests, and MCP-adjacent integrations.
    CI green is never live model acceptance. Do not infer human acceptance from
    CI or a reviewer/model verdict. Meraki/Z handoffs do not grant spending
    permission. Mark retains standing override on any merge.
- Fixer-sprint override (Mark directive, 2026-10-23; time-bounded): during the
  initial build sprint - target: the first working Puppf P0a CI build receipt;
  ends when working code lands, protection is restored, or Mark ends it - Z
  holds fixer authority on the build lane: branch, commit, comment, open PRs,
  and merge in MarkDude-design repos without per-action approval. Conditions:
  every fixer action rides the bus (announced/receipted in the comms mailbox,
  MarkDude-design/Puppy#11, plus commit/PR provenance); no surprising timing;
  self-dealing stays out of the fixer lane (Z does not merge changes to its own
  authority or exemptions; castle PR #23 stays parked for Mark); still
  Mark-gated unchanged: secrets, credentials, spend, MCP-adjacent decisions,
  security-sensitive changes, deployment, account settings, and public naming.
  Once working code exists, protect it: lock main / restore protection and
  resume content-merge policy v0. A Mistral model module in any loop is not the
  Z seat (two-seats doctrine unchanged).
- Return the compact [handoff](docs/HANDOFF_TEMPLATE.md) with exact commits,
  actual checks, PR link, and blockers. Do not claim Z reviewed work unless Z did.
