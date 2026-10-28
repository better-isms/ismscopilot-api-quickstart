import os

from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("ISMS_BASE_URL", "https://api.ismscopilot.com/v1"),
    api_key=os.environ["ISMS_API_KEY"],
)

raw = client.chat.completions.with_raw_response.create(
    model=os.environ.get("ISMS_MODEL", "isms-fast"),
    messages=[
        {
            "role": "user",
            "content": "Which ISO/IEC 27001:2022 Annex A control covers acceptable use of information and other assets? Answer in one line.",
        }
    ],
    extra_body={"ismscopilot": {"frameworks": ["ISO_27001"]}},
)

completion = raw.parse()
print(completion.choices[0].message.content)
print("x-isms-frameworks:", raw.headers.get("x-isms-frameworks"))
