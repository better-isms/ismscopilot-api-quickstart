#!/usr/bin/env bash
set -euo pipefail

: "${ISMS_API_KEY:?Set ISMS_API_KEY to an sk-isms key from platform.ismscopilot.com/keys}"
BASE_URL="${ISMS_BASE_URL:-https://api.ismscopilot.com/v1}"
MODEL="${ISMS_MODEL:-isms-fast}"

headers="$(mktemp)"
body="$(mktemp)"
trap 'rm -f "$headers" "$body"' EXIT

curl -sS -D "$headers" -o "$body" "${BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${ISMS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"${MODEL}"'",
    "messages": [
      {"role": "user", "content": "Which ISO/IEC 27001:2022 Annex A control covers acceptable use of information and other assets? Answer in one line."}
    ],
    "ismscopilot": {"frameworks": ["ISO_27001"]}
  }'

frameworks="$(grep -i '^x-isms-frameworks:' "$headers" | tr -d '\r' | cut -d' ' -f2-)"
printf 'x-isms-frameworks: %s\n' "${frameworks:-<none disclosed>}"
python3 -c 'import json,sys; print(json.load(sys.stdin)["choices"][0]["message"]["content"])' < "$body"
