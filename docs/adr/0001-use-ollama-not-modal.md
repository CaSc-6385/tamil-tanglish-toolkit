# ADR-0001 — Use Ollama on a CPU VPS for Tamil-LLaMA serving, not Modal GPU

- **Status**: Accepted
- **Date**: 2026-05-23
- **Deciders**: schandra@ieee.org
- **Supersedes**: n/a
- **Superseded by**: n/a
- **Related**: docs/PLAN.md §5 (architecture), §8 (cost model); docs/DEPLOYMENT.md §3.3

## Context

PLAN.md v3 specifies a $50/month hard budget cap for all hosted infrastructure. The grammar-correction layer (Sprint 2) needs to serve [chandralabs/tamil-llama](https://github.com/chandralabs/tamil-llama) — a Llama-2-based 7B model with Tamil-specific tokenizer and 145k instruction tuning.

Two viable serving options were considered:

1. **Modal Labs GPU on-demand** — `~$0.60/hr` for an A10G. At even sparse usage (~5 hrs/day cold-started for inference), this is $90/month — already 180% of budget before adding any other costs.
2. **Ollama on a CPU VPS** — runs the quantized GGUF Q4_K_M variant (~4 GB) at 5–10 tokens/sec on a 4 vCPU box. Hetzner CX32 is €4.99/mo (~$5.40 USD).

GPT-4o-mini was considered as an alternative primary corrector but rejected as the sole option because:

- The Tamil-LLaMA model already exists, is fine-tuned for Tamil, and is the user's own prior work — abandoning it would waste demonstrable benchmarks already published in [chandralabs/Tamil-Research-LLM](https://github.com/chandralabs/Tamil-Research-LLM).
- The "Tamil-LLaMA powered" narrative is part of the AOST research story; outsourcing entirely to OpenAI weakens the differentiator.

## Decision

**Serve `chandralabs/tamil-llama` 7B (Q4_K_M GGUF) via Ollama on a Hetzner CX32 (4 vCPU AMD, 8 GB RAM, Frankfurt region) as the primary grammar-correction backend.**

GPT-4o-mini is a _fallback_, gated on:

- Ollama p95 latency > 3 seconds for the request, OR
- Ollama queue depth > 5 concurrent requests, OR
- Ollama health-check failure

Fallback is also hard-budget-capped at $15/month in code (`OPENAI_MONTHLY_BUDGET_USD=15`). Requests exceeding the cap fail with a "service degraded — try again with corrections off" message rather than silently burning money.

## Consequences

### Positive

- **Cost**: ~$5/mo for Ollama + ~$5–10/mo expected GPT fallback = under $15/mo on the grammar layer. Leaves headroom for OCR, Apple Developer fee, and overage buffer within the $50 cap.
- **Latency**: 50-token correction in 1–2 seconds at 5–10 tok/s is acceptable for the "type → correct" UX.
- **Privacy**: User text stays on a single VPS the user controls. No third-party data leakage by default.
- **No vendor lock-in**: Ollama is open source; the GGUF model is downloadable from HuggingFace. Can move to any host in hours.
- **Demonstrates production reuse** of the existing Tamil-LLaMA work.

### Negative

- **Concurrency ceiling**: ~3 concurrent users at p95 < 3s. Scale-up trigger documented in DEPLOYMENT.md §3.3 (upgrade to CX42 at €8/mo if sustained over capacity).
- **Operations burden**: requires managing a Linux VPS (ufw, fail2ban, systemd unit, Hetzner backups). Mitigated by a one-shot `infra/ollama-hetzner/bootstrap.sh` (planned in S2-1).
- **Cold-start latency**: first request after idle may take 5–10s as the model loads into RAM. Mitigated by keeping the Ollama process resident via systemd.
- **No GPU acceleration**: rules out using larger or higher-quality variants (13B, full-precision) without revisiting this decision.

### Reconsider when

- Concurrent user count exceeds 50 sustained (would need GPU or horizontal CPU fleet)
- Quality complaints attributable to Q4 quantization vs. full precision (per native-rater feedback)
- Budget cap is relaxed beyond $50/mo
- A cheaper hosted Tamil model (e.g., a Bedrock or Together.ai endpoint with sub-$10/mo) becomes available

## Alternatives considered

| Option                        | Cost/mo                             | Latency              | Why rejected                                                |
| ----------------------------- | ----------------------------------- | -------------------- | ----------------------------------------------------------- |
| Modal A10G on-demand          | ~$90                                | < 1s                 | Blows the $50 budget by itself                              |
| Replicate cold-start endpoint | ~$0.0001/sec → ~$30 at moderate use | 2–5s with cold-start | Variable cost hard to bound; cold-start UX bad              |
| Together.ai serverless        | ~$0.20/1M tokens → ~$5              | < 1s                 | Locks in third-party; loses "Tamil-LLaMA powered" narrative |
| Self-host on RunPod GPU       | ~$30 (spot)                         | < 1s                 | Spot interruptions; ops complexity higher than Hetzner      |
| GPT-4o-mini only              | ~$10                                | < 1s                 | Abandons user's own Tamil-LLaMA work; weakens narrative     |
| Local-only (user's machine)   | $0                                  | n/a                  | Not usable as a hosted service for kids/parents             |
