# First hosted verification: Windows failure and repair

Original head: `c185c617a265db05d577b29ba9832fb908624224`.
The [original CI run](https://github.com/MarkDude-design/lightbringers-castle/actions/runs/39476815430)
passed Linux on Python 3.10/3.12 and failed Windows on both versions. The
workflow uploaded dedicated verifier summaries/logs even for failed jobs.
Those artifacts have seven-day retention; this note retains the diagnostic
facts rather than assuming the hosted logs will exist forever.

The Windows 3.12 artifact `offline-windows-latest-py3.12` (ID `12287929890`)
was downloaded and its archive SHA-256 independently matched GitHub's digest:
`242ae913eccae305ef3081c69c9fd1143013186fdfd0d9c22dd037c9856b667d`.
Its two failed checks were:

- Conversation/project tests: 73 discovered and run, one failure, no skips.
  `test_packet_hash_is_frozen_and_content_sensitive` expected LF source text
  but received CRLF. The fixture used a platform-translating text write.
- Runtime probe tests: seven discovered and run, one failure, no skips.
  `test_real_child_output_and_termination` reported `TimeoutError: Child did
  not emit readiness within 5 seconds`. Cleanup later retained stdout
  `runtime-probe-child-ready\n`, with `terminate_sent: false`,
  `kill_fallback: true`, and `reaped: true`.

Compilation (13 files), tracked JSON (24 files), JavaScript (four files), CLI
help (two commands), and whitespace checks all passed in that Windows job.
These observations describe the original failure, not a successful repair.

## Repair boundary

The test fixture now writes explicit LF bytes. A regression checks that CRLF
source bytes remain CRLF in a frozen packet, with their original byte count
and SHA-256. Production packet hashing is unchanged.

The fixed-code child probe reads stdout/stderr through one reader per pipe
and signals readiness from the actual stdout marker. It no longer depends on
`communicate()` exposing partial output in `TimeoutExpired`, which differs
across platforms. The five-second readiness/normal-exit limits and two-second
termination/kill waits remain. Output-reader joins are also bounded. Cleanup
records output, process reaping, and errors on both success and failure.

Regression tests cover real child output/termination, independence from
`communicate()` timeout output, readiness failure cleanup, termination-timeout
kill fallback, and premature exit. All tests remain enabled. This repair adds
no credentials, network access, live inference, or deployment.

Run `python scripts/verify.py` locally; hosted Linux/Windows matrix results
must be observed for the repaired head before claiming platform acceptance.
