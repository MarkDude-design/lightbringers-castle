# Castle/Ring development thread — historical handoff

Archived: 2026-10-28. This selected project history is archival data. It does not change runtime, policy, acceptance decisions, or spending authority. Current main, current repository instructions, and authoritative private receipts override old plans. No raw live transcript or credential is included.

## Scope and evidence

The source conversation covered the read_room loop, budgeted project tasks, offline verification, paid attempts, the eligibility repair, a scripted theater, and Team handoffs. User-carried Codex reports are reported evidence unless an independent check is explicitly noted. Verification performed for a historical commit is not a fresh check of current main.

Private artifact download paths supplied from other execution environments were often unavailable to Meraki. Their absence was not a claim that evidence never existed. Do not fabricate or reconstruct native API responses from these summaries.

## Milestones and commits carried in the thread

| Item | Historical identifier | Result / qualification |
| --- | --- | --- |
| PR #4 reviewed head | 774b6f4ee86aa9e7acf5b80af3f20cdff358a5a3 | Bounded OpenRouter read_room loop; reported 35 offline tests; exact-model Windows live transaction inspected in the carried review receipt |
| PR #4 merge | 5ac7bec0380215bb41cd5624cae2cf960001dca9 | Mark reported tested files matched merge; no deployment |
| Budgeted Project Tasks v0 | e92d0aa46e1b8d0d99cf079c6bc6d2f53279f423 | Frozen sources, worker/reviewer proposals, cost receipts, offline Z export, hash-bound human decision; reported 64 tests |
| Paid preflight | 72ee5cb8da224d20310bb61aad5bc9539678bfdb | Initially blocked by metadata/proxy and absent secure credential in that environment; missing price was not zero; reported 70 tests |
| Shared verifier branch | c185c617a265db05d577b29ba9832fb908624224 | Agent-owned offline verification and Linux/Windows CI; original reported 80 tests; Windows issues were repaired later |
| PR #9 head | cb5158ab12eac0e700b99a616af736582d176723 | Reported 87 tests; dry-run estimate $0.0150969 under $0.05; live qualification remained separate |
| PR #11 receipt head | 61d2da3a2ca134e8b6f717b16e6ed2d703132916 | First paid failure: worker cap exhausted; one call |
| PR #13 receipt head | 2c3e10e70e626efb7ee0b34582b89e18a27b148e | Low-effort JSON rejected; no reviewer |
| PR #15 receipt head | 36e6357bc8d40bb6ad307c2c13ba47ff66a593a2 | Guided result rejected for empty acceptance_checks |
| PR #16 reviewed head | 6a4c3dc91352b919cd3f2a42b43252a1b32d352c | Exposed list bounds and focused the host finding; 104 tests and four CI jobs checked in the review history |
| Source main after #16 | 333168088a6db1f7e9ba5ef0991b4b79f7b5b7f1 | Source for Astra offline exercise and next live packet |
| PR #17 receipt head | 08bb424e612989de6ccc2312ef6b171f2bd61a38 | First schema-valid worker/reviewer pair; needs_changes; receipt only |
| PR #18 repair head | 7e00cc72aa5ee8c5e5c6b33cd5ca30002f120ef5 | Eligibility OSError skip without retries; Meraki independently checked 108 tests/static and four CI jobs |

## PR #4 acceptance boundary

Agreed v0 allowed a tools-only/null-content first response followed by successful local read_room execution and a grounded final response. Native assistant tool-call message and continuation metadata were preserved. Malformed/duplicate/reused tool IDs, STOP/caps, malformed shapes, duplicate argument fields, identity drift, provenance, and credential redaction were the bounded review categories. Broader router/retry/token-budget/CLI work remained outside that PR.

Carried live session: talk-be22334277ea496ba5f6d1f863454984. Requested/returned model on both calls: nvidia/nemotron-3.5-lightning:free. Model requested courtyard; the supplied receipt says data matched the reviewed courtyard.json. Final answer cited the stored name and the signs/armor details. Two successful calls, one tool execution, one final reply; 1,634 reported tokens; provider-reported cost $0, not an account-billing audit. The milestone established one working Windows/OpenRouter/read_room transaction, not general model or deployment readiness. Process exit status was not in JSONL; supplied console showed normal completion.

## Paid task receipt history

Task: room-registry-error-ticket-v0; original cumulative local budget $0.05.

| Attempt | Observed/reported failure or result | Call cost USD | Cumulative USD |
| --- | --- | ---: | ---: |
| Default effort | 2,048 completion cap; 2,045 reasoning; no final ticket; one call | 0.000369954 | 0.000369954 |
| Low effort | 333 reasoning tokens; JSON missing uncertainties; line 4,842 cited in a 125-line file; one call | 0.000253908 | 0.000623862 |
| Guided low | Fields and ranges passed; acceptance_checks empty; one call | 0.000224352 | 0.000848214 |
| Focused batch | Worker $0.000225162 + reviewer $0.000220086; valid pair; needs_changes | 0.000445248 | 0.001293462 |

The focused batch stopped at its first valid pair after one attempt/two calls, within authorization for up to three attempts/six calls. Remaining attempts were not automatically available after that stop. Human acceptance remained unset and accepted artifacts zero in the carried ledger. Cost per accepted result was unavailable. Local budgeting was not represented as a guaranteed provider billing ceiling.

The reviewer reportedly restated the original gap without explaining the required revision. Host review separately found missing attribution, FileNotFoundError-only coverage, and insufficient test scope. Schema validity did not settle substance.

## Host finding and bounded repair

Original room_paths checked is_file and a subsequent size stat without catching eligibility OSError. read_room called room_paths before its read-time handler. The host/Codex synthetic probe identified this; it was not a worker discovery.

Approved behavior: catch only OSError from per-candidate file/size eligibility; skip that candidate and continue, retaining healthy entries. One eligibility evaluation per candidate per pass; zero retries. Skipped entries yield the existing unknown_room result and disappear from catalog enumeration. Preserve containment, ID, regular-file and 64 KiB rules, order, existing read-time errors, contents, linkage, and CLI exits. Resolution/iteration failures and later filesystem races remained outside the repair.

Actual implementation scope: castle/room_tools.py, tests/test_talk.py, tests/test_project_tasks.py, plus a separate host brief. The existing host fixture was transitioned from asserting escape to checking the handled result while retaining injection proof.

Meraki independently loaded the trusted original function in memory: all 27 injected-error subcases failed under the original; the repaired implementation passed those selected methods. The reviewed head passed the complete 108-test/static verifier and four hosted jobs. The host brief's frozen hash and three original source hashes were checked. Codex's statement that all 19 private ledger files remained byte-identical was reported evidence to Meraki, not an independent private-ledger inspection.

## Astra contribution

Astra performed a separate hosted/offline ticket exercise against packet bd03f4c828119910546fc8c27cae61ef8460dcd2a59cbe5ec0ea985120e4131d. Its schema, hash, source bytes, and references were independently checked at the time. This was not an OpenRouter receipt, a new task-ledger attempt, human acceptance, or a measured zero-cost run.

Astra also proposed a private offline task dossier: show all attempts, failures, known/unknown costs, source/worker hashes, reviewer verdict, and separate human decision. The existing export-z path did not carry the full failure/cost history. This was a recommendation, not implemented functionality in the source conversation.

## Packet constraints discovered during handoff

The v0 packet required allowed_files to be supplied source files, and those sources to exist. Oversized project-task source could not be silently truncated or admitted by increasing the 32 KiB cap. The repair used a separately identified host implementation brief with full file hashes and bounded excerpts. That brief did not masquerade as a runner packet or overwrite the original model ticket.

## Later policy and parallel work

The attached Z review described an expanded static theater, tiered content merge authority, and economy unit-price lanes. A later repository read confirmed those features on then-current main. Historical exemption dates and planned extensions were not new grants. Current AGENTS.md and current lane code govern actual operations.

The continuing Z seat and a Mistral model module have separate roles and evidence. Module execution is not proof the Z seat reviewed the result. Deterministic code calculates totals; a model may summarize them. Digests and automated delivery have separate effects on human ferry count.

## Continue from current code

Use the current repository's instructions and receipts. Do not rerun historical live requests, reopen old spend allowances, accept original rejected tickets because a later repair merged, or mistake this archival PR for a new feature task.

END CASTLE PROJECT HISTORY
