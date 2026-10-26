# TokenGate prefill receipt (external evidence, 2026-10-26)

Dated external-evidence note attached to the model-lane policy
(`castle/PROJECT_TASKS.md`, "Model lanes (v0)", PR #22). Content-only.
No code, configuration, pricing map, task ledger, or CI changed by this note.

## What

**TokenGate: Adapting LLMs for Fast and Memory-Efficient Prefill with Learned
Token Pruning.** Liana Patel, Rishabh Ranjan, Ion Stoica, Matei Zaharia,
Carlos Guestrin (Stanford / UC Berkeley). arXiv 2610.26754, appeared 2026-10-25.
Code and checkpoints under Apache-2.0.

A small MLP gate and LoRA (r=16) added to Qwen3-1.7B / Qwen3.5-2B. Layers below
the gate process all tokens; the gate scores each token; layers above process
only the top-K and never create KV entries for pruned tokens. Top-K selection is
made differentiable with a Mixture-of-Experts-style logit bias. Only the
document part of the prompt is prunable; the question is never pruned.

## Self-reported numbers (lab conditions)

- 1.4x-11.3x faster time-to-first-token; 1.5x-3.4x lower peak prefill memory.
- Contexts to 128k; timings on 1 A100 at batch size 1.
- Best case: needle-in-a-haystack 16k, 11.3x TTFT, 3.42x memory. TTFT gain
  reaches 13.0x at 128k on a gate trained at 16k. Some tasks see only 1.4x.

## Receipts caveat (why the aggregator TL;DR overclaims)

Headline says "no accuracy loss." The paper's own best-setting numbers are
95% of full-context accuracy on 2WikiMultihopQA and "within 6%" for early-layer
gating on the hybrid model. That is a small accuracy tradeoff at aggressive
settings, not zero. Cite the paper, not summary write-ups.

## Relation to this repository

Complements, does not change, the model-lane policy. The lane bounds unit price
at plan time, before transport (routing layer). TokenGate prunes inside prefill
(attention layer). Same doctrine, different layer: reduce the cost of getting to
an accepted result rather than raising throughput for its own sake.

Not deployable here in v0: it requires self-hosted weights; OpenRouter-routed
calls cannot apply it. Relevance rises only if a self-hosted local-model lane is
added later. Until then this note is evidence about where the input-cost floor
is heading, not a configuration proposal.

## Craft note kept

"Only the document is prunable - the question is never pruned."

## Boundaries

- No live model request, deployment, or pricing observation is claimed.
- No lane caps, budget, task ID, or ledger fields changed.
- Merged under content-merge policy v0 (AGENTS.md, 2026-10-21).
