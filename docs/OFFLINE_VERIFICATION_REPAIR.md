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

## Follow-up: Python 3.10 Windows process startup

The [first repaired-head run](https://github.com/MarkDude-design/lightbringers-castle/actions/runs/39482214063)
on `a03c51a056b460dd9009486ea0475aabdc5cb3aa` passed both Linux jobs and
Windows 3.12. Windows 3.10 passed all 74 conversation/project/verifier tests
but failed four of 11 runtime-probe tests because child creation raised
`OSError: [WinError 87] The parameter is incorrect` before launch.

Its artifact `offline-windows-latest-py3.10` (ID `12292250577`) was downloaded;
archive SHA-256 matched the reported digest
`333f0eaccc008a5540a0332ca8892f2c32f2ff483dd42547d446910e2a1cc7c5`.
The remaining compilation, JSON, JavaScript, CLI, and whitespace checks passed.

The original empty child environment is now empty on POSIX and explicitly
allowlists only `SystemRoot` on Windows. Python's
[subprocess documentation](https://docs.python.org/3.10/library/subprocess.html#subprocess.Popen)
requires an explicitly supplied environment to include variables needed for
program startup, including Windows `SystemRoot` for side-by-side assemblies.
No API keys, tokens, proxies, or PATH are inherited. Missing `SystemRoot`
fails before launch. Regression fixtures verify the exact environment allowlist
and the missing-variable failure. This is an explicit compatibility change to
the child environment boundary; it does not authorize broader inheritance.
