---
name: ismscopilot-api
description: Call the ISMS Copilot model API (OpenAI-compatible chat completions with compliance framework modules built in) for ISO 27001, SOC 2, GDPR, NIS 2, DORA, the EU AI Act and other GRC questions. Use when a task needs a compliance-grounded answer, a per-framework or per-country answer, or bulk GRC text work from code, a script or a workflow, and an `sk-isms-` key is available or can be created.
---

# ISMS Copilot API

An OpenAI-compatible chat completions endpoint for compliance work. Before generation, the server injects curated framework modules (ISO 27001, SOC 2, GDPR, DORA, a NIS 2 module for each EU member state, and more) and tells you which ones it used.

## Connect

- Base URL: `https://api.ismscopilot.com/v1`
- Key: `sk-isms-...`, created by the human at https://platform.ismscopilot.com/keys. Read it from an environment variable (`ISMS_API_KEY`). Never print it, log it or commit it. A `pat-isms-` token does not work here.
- You cannot create the account, sign in or pay for the human. If there is no key, ask the human to sign up at https://platform.ismscopilot.com/signup and create one.
- Credit: while the offer runs, an eligible new account (no API credit history) gets its first USD 2 free when it creates its first key. After that, the human adds prepaid credit at https://platform.ismscopilot.com/credits. Rates: https://platform.ismscopilot.com/pricing

Any OpenAI SDK works by changing the base URL:

```python
import os
from openai import OpenAI

client = OpenAI(base_url="https://api.ismscopilot.com/v1", api_key=os.environ["ISMS_API_KEY"])
raw = client.chat.completions.with_raw_response.create(
    model="isms-fast:ISO_27001",
    messages=[{"role": "user", "content": "Which ISO 27001 control covers supplier relationships?"}],
)
print(raw.parse().choices[0].message.content)
print(raw.headers.get("x-isms-frameworks"))  # ISO_27001
```

## Pick the model

| Alias | Use it for |
| --- | --- |
| `isms-fast` | Default. Fast answers. |
| `isms-thinking` | Harder questions; uses more tokens. `max_tokens` below 1024 is raised to 1024. |
| `isms-fast-eu`, `isms-thinking-eu` | Same, with AI inference on Mistral in the EU. |
| `isms-mini` | The cheap lane for bulk formatting, extraction and classification. Use it for loops over many items. |

## Pick the framework for each call

Pin the module whenever you know the framework. Without a pin, the API detects framework names in the user messages and the last assistant turn, not in system messages (`auto`), and a bare question such as "help me with 5.23" can get no module at all.

1. **In the model name** (works in any tool that only lets you set a model string): an alias, a colon, then up to 8 comma-separated catalog ids. Same price as the base alias.
   - `isms-fast:NIS_2_DE`
   - `isms-fast-eu:GDPR,ISO_27001`
   - `isms-mini:SOC_2`
2. **In the request body** (when you control the JSON): `"ismscopilot": {"frameworks": ["NIS_2_DE"]}`. With the OpenAI Python SDK: `extra_body={"ismscopilot": {"frameworks": [...]}}`. `"none"` turns injection off (only possible here).

Use one or the other, never both: a suffix plus `ismscopilot.frameworks` returns `400 framework_conflict`.

Catalog ids are exact and case-sensitive. List them (no key needed): `GET https://api.ismscopilot.com/v1/frameworks`. Check an id there before you use it; an unknown id returns `400 framework_not_found`. `:none` and `:auto` are not valid suffixes. Docs: https://docs.ismscopilot.com/docs/api/framework-knowledge.md

For one question across several countries, send one request per country, each pinned to that country's module (`NIS_2_NL`, `NIS_2_IT`, ...).

## Read what ran

- The `x-isms-frameworks` response header lists the injected modules. Keep it next to the answer when you need a record.
- The response `model` field is the base alias (`isms-fast`), even when you sent a suffix.
- `GET /v1/models` lists the five aliases only. `GET /v1/models/isms-fast:NIS_2_DE` returns `200` for a valid suffixed id (`404` while extensions are switched off).

## Limits

- Text in, text out. No tool or function calling, no JSON mode (`response_format`), no images, `n` is 1. Streaming works. Sending `tools` returns `400`: keep your own model as the orchestrator and call this API as a plain completion step.
- Ask for structure in the prompt and parse the text yourself.
- 120 requests per minute per key. On `429 rate_limit_exceeded`, wait `Retry-After`. On `429 insufficient_quota` the balance is empty: tell the human, do not retry.
- Before a large loop, estimate the cost and confirm with the human; suggest a per-key spend cap in the console.
- Answers are guidance, not legal advice or an audit opinion. Recommend human review where the stakes require it.

## More

- Errors: https://docs.ismscopilot.com/docs/api/errors.md
- Coding agents: https://docs.ismscopilot.com/docs/api/use-in-coding-agents.md
- All API docs: https://docs.ismscopilot.com/docs/api
