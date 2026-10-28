"""Rerun a slice of the ISMS-Bench scaffold benchmark with your own key.

Two arms per task, same model, same question:

  naked   ismscopilot: {"frameworks": "none", "system": "none"}
          No framework module and no ISMS Copilot persona: the model alone.
  module  ismscopilot: {"frameworks": [<task framework>], "system": "none"}
          The same model with the curated framework module injected.

Default model: isms-mini (GLM 5.3 Flash, the model the 2026-09-02 benchmark
used). A full run is 14 requests on your prepaid credit; use --dry-run to see
the requests and a token estimate first.

    python3 bench-slice/rerun.py --dry-run
    python3 bench-slice/rerun.py --yes
    python3 bench-slice/rerun.py --yes --model isms-fast --tasks t01-iso-a8.16-monitoring,t19-trap-gdpr-art103

What it scores, honestly: a deterministic check only. It counts expected
citations found, flags identifiers that cannot exist in the framework (for
example ISO 27001:2022 A.8.40 or GDPR Art. 103), and for the trap task checks
whether the answer says the article does not exist. It is not the published
benchmark's scoring: that used frozen rubrics and a blind judge model from a
different vendor. Read the answers in results/ before drawing conclusions.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
TASKS = json.loads((HERE / "tasks.json").read_text())["tasks"]

# Upper bounds used to flag identifiers that cannot exist (not a full registry).
ISO27001_THEME_MAX = {5: 37, 6: 8, 7: 14, 8: 34}
ISO42001_GROUPS = range(2, 11)  # A.2 to A.10
MAX_ARTICLE = {"GDPR": 99, "DORA": 64}

# Rough per-request token shape for the estimate (input, output).
EST_TOKENS = {"naked": (700, 900), "module": (15000, 900)}

ARMS = {
    "naked": lambda fw: {"frameworks": "none", "system": "none"},
    "module": lambda fw: {"frameworks": [fw], "system": "none"},
}


def norm(text):
    text = text.replace(" ", " ")
    text = re.sub(r"\bArticles?\s+(?=\d)", "Art. ", text)
    text = re.sub(r"\bArt\.?\s*(?=\d)", "Art. ", text)
    return text


def has_citation(text, cite):
    pattern = re.escape(cite)
    if re.search(r"\d$", cite):
        pattern += r"(?!\d)"
    return re.search(r"(?<![\w.])" + pattern, text) is not None


def impossible_ids(text, framework):
    bad = set()
    if framework == "ISO_27001":
        for m in re.finditer(r"\bA\.(\d{1,2})\.(\d{1,3})(\.\d{1,2})?(?![\d.]\d)", text):
            theme, ctl, third = int(m.group(1)), int(m.group(2)), m.group(3)
            if theme in ISO27001_THEME_MAX and (third or ctl > ISO27001_THEME_MAX[theme] or ctl == 0):
                bad.add(m.group(0))
            elif 9 <= theme <= 18:
                bad.add(m.group(0) + " (2013 numbering)")
    elif framework == "ISO_42001":
        for m in re.finditer(r"\bA\.(\d{1,2})(?:\.\d+)*", text):
            if int(m.group(1)) not in ISO42001_GROUPS:
                bad.add(m.group(0))
    elif framework in MAX_ARTICLE:
        for m in re.finditer(r"\bArt\. (\d{1,3})", text):
            if int(m.group(1)) > MAX_ARTICLE[framework]:
                bad.add(m.group(0))
    elif framework == "SOC_2":
        for m in re.finditer(r"\bCC(\d{1,2})\.\d+", text):
            if int(m.group(1)) > 9:
                bad.add(m.group(0))
    return sorted(bad)


def flags_nonexistent(text):
    return re.search(
        r"(does not|doesn't|did not) exist|no (such )?article 103|not an? (real|existing)|only (has )?99 articles|99 articles",
        text, re.I) is not None


def score(task, answer):
    text = norm(answer)
    found = [c for c in task["expected_citations"] if has_citation(text, c)]
    bad = impossible_ids(text, task["framework"])
    if task["tier"] == "trap":
        # Mentioning Art. 103 to refute it is the right behaviour, so the trap is
        # scored on the refusal, not on the impossible-id list.
        return {"trap_flagged": flags_nonexistent(answer), "impossible_ids": bad}
    return {"citations_found": f"{len(found)}/{len(task['expected_citations'])}", "missing": [c for c in task["expected_citations"] if c not in found], "impossible_ids": bad}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=os.environ.get("ISMS_MODEL", "isms-mini"))
    ap.add_argument("--tasks", help="comma-separated task ids (default: all)")
    ap.add_argument("--dry-run", action="store_true", help="print the requests and a token estimate, call nothing")
    ap.add_argument("--yes", action="store_true", help="run without the confirmation prompt")
    args = ap.parse_args()

    tasks = TASKS
    if args.tasks:
        wanted = set(args.tasks.split(","))
        tasks = [t for t in TASKS if t["id"] in wanted]
        if not tasks:
            sys.exit(f"No task matches {args.tasks}")

    est_in = sum(EST_TOKENS[a][0] for a in ARMS) * len(tasks)
    est_out = sum(EST_TOKENS[a][1] for a in ARMS) * len(tasks)
    print(f"{len(tasks)} tasks x {len(ARMS)} arms on {args.model}: about {est_in:,} input and {est_out:,} output tokens "
          "(estimate; thinking aliases use more). Rates: https://platform.ismscopilot.com/pricing")

    if args.dry_run:
        for t in tasks:
            for arm, ext in ARMS.items():
                print(json.dumps({"task": t["id"], "arm": arm, "model": args.model, "ismscopilot": ext(t["framework"]), "messages": [{"role": "user", "content": t["question"]}]}))
        return
    if not args.yes and input("Run it? [y/N] ").strip().lower() != "y":
        return

    from openai import OpenAI  # imported here so --dry-run works without the package

    client = OpenAI(
        base_url=os.environ.get("ISMS_BASE_URL", "https://api.ismscopilot.com/v1"),
        api_key=os.environ["ISMS_API_KEY"],
    )
    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{time.strftime('%Y%m%d-%H%M%S')}-{args.model}.jsonl"

    rows = []
    with out_path.open("w") as out:
        for t in tasks:
            for arm, ext in ARMS.items():
                raw = client.chat.completions.with_raw_response.create(
                    model=args.model,
                    messages=[{"role": "user", "content": t["question"]}],
                    temperature=0,
                    extra_body={"ismscopilot": ext(t["framework"])},
                )
                completion = raw.parse()
                answer = completion.choices[0].message.content or ""
                result = {"task": t["id"], "arm": arm, "model": args.model,
                          "x_isms_frameworks": raw.headers.get("x-isms-frameworks"),
                          "usage": {"input": completion.usage.prompt_tokens, "output": completion.usage.completion_tokens},
                          "check": score(t, answer), "answer": answer}
                out.write(json.dumps(result) + "\n")
                rows.append(result)
                print(f"{t['id']:<32} {arm:<7} {json.dumps(result['check'])}")

    print(f"\nAnswers and checks: {out_path}")
    print("Deterministic checks only. The published benchmark used rubrics and a blind judge; read the answers.")


if __name__ == "__main__":
    main()
