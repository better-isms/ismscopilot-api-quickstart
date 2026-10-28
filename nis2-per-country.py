"""Ask the same NIS 2 question for customers in different EU countries.

Each request pins only that customer's national NIS 2 module, so the answers
stand on different national laws and never mix. Prints the answer and the
modules the API disclosed for each country.

    python3 nis2-per-country.py            # NL, IT, BE
    python3 nis2-per-country.py NL         # one country
    ISMS_MODEL=isms-fast-eu python3 nis2-per-country.py IT

Every request draws on your prepaid credit. Country codes map to catalog ids
named NIS_2_<code>; check the live catalog (GET /v1/frameworks, no key needed)
before adding one.
"""

import os
import sys

from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("ISMS_BASE_URL", "https://api.ismscopilot.com/v1"),
    api_key=os.environ["ISMS_API_KEY"],
)
MODEL = os.environ.get("ISMS_MODEL", "isms-fast")

QUESTION = (
    "We are a managed IT service provider with 80 staff. Under our national NIS 2 law, "
    "are we in scope, which incident reports do we owe and to which authority, and by when? "
    "Name the national law and the articles. Keep it under 200 words."
)

countries = [c.upper() for c in sys.argv[1:]] or ["NL", "IT", "BE"]

for country in countries:
    raw = client.chat.completions.with_raw_response.create(
        model=MODEL,
        messages=[{"role": "user", "content": QUESTION}],
        extra_body={"ismscopilot": {"frameworks": [f"NIS_2_{country}"]}},
    )
    completion = raw.parse()
    print(f"=== {country} | x-isms-frameworks: {raw.headers.get('x-isms-frameworks')}")
    print(completion.choices[0].message.content.strip())
    print(f"(tokens: {completion.usage.prompt_tokens} in, {completion.usage.completion_tokens} out)\n")
