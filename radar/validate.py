"""Step 3 - deterministic validator. Runs BEFORE the critic agent.

Cheap deterministic checks first, expensive LLM judgement second - the
same ordering that keeps production agent pipelines affordable. Fails the
run loudly instead of publishing something wrong quietly.
"""
import json
import re
import sys

HYPE = [
    "game-changer", "revolutionary", "seamless", "supercharge", "unlock",
    "next level", "mind-blowing", "insane", "10x your", "you won't believe",
]

def main() -> None:
    draft = open("artifacts/draft.md", encoding="utf-8").read()
    signals = json.load(open("artifacts/signals.json", encoding="utf-8"))

    problems = []
    low = draft.lower()
    for w in HYPE:
        if w in low:
            problems.append(f"hype vocabulary: '{w}'")

    markers = {int(n) for n in re.findall(r"\[(\d+)\]", draft)}
    bad = {n for n in markers if not 1 <= n <= len(signals)}
    if bad:
        problems.append(f"markers outside the source list: {sorted(bad)}")
    if len(markers - bad) < 3:
        problems.append(f"only {len(markers - bad)} valid citations - need at least 3")
    if re.search(r"\((https?://[^\s)]+)\)", draft):
        problems.append("agent wrote raw urls - it must only use [n] markers")

    if len(draft.split()) < 80:
        problems.append("draft is too thin to be a brief")

    if problems:
        with open("artifacts/critic.json", "w", encoding="utf-8") as f:
            json.dump({"verdict": "fail", "reasons": problems}, f, indent=2)
        sys.exit("validate: FAIL\n- " + "\n- ".join(problems))
    print(f"validate: pass ({len(markers)} citation markers, all mapped to collected sources)")

if __name__ == "__main__":
    main()
