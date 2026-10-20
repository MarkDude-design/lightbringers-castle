# Contributing to Lightbringer's Castle

Welcome to the Castle! Here's how to add your own bots, rooms, and jokes.

## Development and verification

Read [AGENTS.md](AGENTS.md). Agents handle routine Git/testing and return an
isolated, reviewable draft PR; Mark owns merge and human acceptance. Inspect
current main and open PRs first. Keep unrelated work on its own branch.

Use Python 3.10+, Git, and Node.js 24. No package installation or API keys are
needed for offline verification. Stage intended new source files first: source
checks use Git's tracked inventory, not ignored run directories or untracked
private files. From the checkout root, run the same command locally and in CI:

```sh
python scripts/verify.py
```

Windows may use `py -3 scripts/verify.py`. Symlink fixtures require Windows
Developer Mode or the symlink privilege; CI enables Developer Mode on its
disposable hosted runner. Missing prerequisites are failures, not skipped tests.

The command runs both existing test suites, compiles tracked Python, parses
tracked JSON, checks the Castle JavaScript scripts, invokes both CLI help
commands, and checks committed, staged, and unstaged whitespace. Counts are
discovered, not fixed totals. Every independent check runs after another fails;
the exit code is nonzero if any required check fails. Zero-test suites, skips,
and expected failures cannot silently produce green verification.

Evidence goes into a new ignored `.verification/<run-id>/` directory: one log
per check and `summary.json`, including actual test outcomes/counts, source
commit, platform/runtime versions, and diff base. Existing evidence is never
overwritten. To select a PR/push range or a new evidence directory explicitly:

```sh
python scripts/verify.py --base BASE_SHA --output .verification/my-new-run
```

Default diff base is the merge base with local `origin/main`. On main (or with
no origin), check the preceding commit; a root/initial push uses an empty tree.
CI supplies the PR base SHA or main push's before SHA and fetches full history.
No source checkout/reset, model request, live task, account change, or ledger
mutation is part of verification. Time-sensitive tests use labeled synthetic
fixtures, not refreshed historical quotes or a real task run.

Test subprocesses receive an allowlisted environment without API tokens/keys
or proxy credentials and a Python socket audit guard. This is an offline test
guard, not an operating-system network sandbox. Never add live inference to
tests or CI, and never wire model credentials into push/PR workflows. CI uploads
only the dedicated verifier summary/logs, never `.task-runs`, `.talk-runs`, or
an entire checkout. Review logs before sharing outside the project.

GitHub Actions uses this same command on Linux/Windows with Python 3.10/3.12
and Node 24. Matrix jobs continue independently. Failed evidence is uploaded
with a short retention period. Hosted Windows/other-version success must be
observed in actual CI; a local Linux pass is not evidence of those jobs.
**CI success is not live model acceptance.**

Preserve task IDs, ledgers, unknown costs, failures, and unresolved attempts.
Do not delete a lock, reset accounting, or retry a possibly completed request
as a verification fix. Hand off using [this compact format](docs/HANDOFF_TEMPLATE.md),
including failures/blockers and which commands actually ran. If publishing is
blocked, preserve the tested branch, prepare the PR description, and report
the precise blocker; Mark should not have to repeat your local checks.

## Adding a New Bot

1. Add to `registry/bots.csv`
2. Create `castle/bots/{bot_id}.json`
3. Add asset reference to `registry/assets.json`

## Adding a New Room

1. Add to `registry/rooms.csv`
2. Create `castle/rooms/{room_id}.json`

## Adding a Joke

Add new entries to a room's `jokes` array:

```json
{
  "setup": "Your setup",
  "punchline": "Your punchline"
}
```

## Scaling Notes

- Keep the CSV files as a master index.
- Use JSON for richer details.
- Keep assets mapped via `asset_key`.
- Organize content by room or bot type as the project grows.
