# ISMS Copilot API examples

The compliance API: cost-effective models with compliance knowledge built in. This repo is the shortest path from a key to a first answer, plus two things worth running next: the same NIS 2 question for customers in different EU countries, and a slice of our published benchmark you can rerun with your own key.

The endpoint is an OpenAI-compatible chat completions API, text-only subset, so the official OpenAI SDKs work by changing the base URL. Before generation, the API injects curated framework modules (ISO 27001, SOC 2, GDPR, DORA, a NIS 2 module for each EU member state, and more), and every successful response names the modules it used in the `x-isms-frameworks` header.

## Setup

1. Create a key at https://platform.ismscopilot.com/keys (shown once, prefix `sk-isms-`). New API accounts get their first answers free while the offer runs; after that, add prepaid credit at https://platform.ismscopilot.com/credits. Rates: https://platform.ismscopilot.com/pricing
2. Export the key. Never commit it; `.env` is in `.gitignore`.

```bash
export ISMS_API_KEY=sk-isms-...
```

Optional: `ISMS_MODEL` (default `isms-fast`) and `ISMS_BASE_URL` (default `https://api.ismscopilot.com/v1`). See `.env.example`.

## 1. First call

Each script asks one ISO 27001 question with the `ISO_27001` module pinned, then prints the answer and the `x-isms-frameworks` disclosure.

```bash
bash first-call.sh                                   # curl

pip install -r requirements.txt
python3 first-call.py                                # Python

npm install
npx tsx first-call.ts                                # TypeScript
```

## 2. One question, three countries

```bash
python3 nis2-per-country.py          # NL, IT, BE
python3 nis2-per-country.py IT       # one country
```

The same question goes out once per country, each request pinned to that country's NIS 2 module (`NIS_2_NL`, `NIS_2_IT`, `NIS_2_BE`). Nothing is shared between requests, so adding a country never changes another country's answer. This is the pattern for compliance platforms with customers in several countries: https://docs.ismscopilot.com/docs/api/multi-tenant-integration

## 3. Rerun a slice of the benchmark

On 2026-09-02 we ran a pre-registered, 20-task benchmark: the same base model with and without the knowledge module, judged blind. Write-up, losses included: https://www.ismscopilot.com/blog/we-benchmarked-our-compliance-stack-against-the-naked-model

`bench-slice/` holds 7 of those 20 tasks, word for word, and a script that asks each one twice on your key: once with no module and no ISMS Copilot persona (`naked`), once with the task's module pinned (`module`). Default model: `isms-mini`, the model the benchmark used.

```bash
python3 bench-slice/rerun.py --dry-run     # the 14 requests and a token estimate, no calls
python3 bench-slice/rerun.py --yes         # run them on your credit
```

It prints a deterministic check per answer (expected citations found, identifiers that cannot exist such as ISO 27001:2022 A.8.40 or GDPR Art. 103, and whether the trap answer refuses the false premise) and writes every answer to `bench-slice/results/`. That check is not the benchmark's scoring, which used frozen rubrics and a judge model from another vendor. Read the answers. One sample per arm, temperature 0: your numbers will not match ours exactly.

## Limits worth knowing before you integrate

- Text in, text out: no tool or function calling, no JSON mode, no images, `n` is 1. Streaming works. Agent frameworks that send tool definitions get a `400`; keep a general model as the orchestrator and call this API as a plain completion step.
- Pin frameworks when you know them. `auto` detection reads user messages and the last assistant turn, not system messages. Up to 8 ids per request; valid ids: `GET https://api.ismscopilot.com/v1/frameworks` (no key needed).
- Thinking aliases raise `max_tokens` below 1024 to 1024.
- For unattended loops, set a per-key spend cap in the console.
- Prompts and answers are not stored as records (Zero Data Retention): https://docs.ismscopilot.com/docs/api/zero-data-retention

## Model aliases

| Alias | Use it for |
| --- | --- |
| `isms-fast` | Fast answers, global path |
| `isms-thinking` | Harder questions; more tokens |
| `isms-fast-eu`, `isms-thinking-eu` | The same, with AI inference on Mistral in the EU |
| `isms-mini` | High-volume formatting, extraction and classification, global path |

## Guides

- Errors and codes: https://docs.ismscopilot.com/docs/api/errors
- LangChain: https://docs.ismscopilot.com/docs/api/langchain
- Vercel AI SDK: https://docs.ismscopilot.com/docs/api/vercel-ai-sdk
- n8n: https://docs.ismscopilot.com/docs/api/n8n
- LiteLLM proxy: https://docs.ismscopilot.com/docs/api/litellm
- Cloudflare AI Gateway: https://docs.ismscopilot.com/docs/api/cloudflare-ai-gateway
- Coding agents (sub-agent step): https://docs.ismscopilot.com/docs/api/use-in-coding-agents
- All API docs: https://docs.ismscopilot.com/docs/api
