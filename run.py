"""ctaio-radar - orchestrator.

collect -> draft (agent) -> validate (deterministic) -> critique (agent) -> publish

Each step reads only the previous step's artifact on disk, so every
handoff is inspectable after the run and any step can be re-run alone.
"""
import datetime
import os
import shutil
import subprocess
import sys

STEPS = [
    ("collect", [sys.executable, "radar/collect.py"]),
    ("draft", [sys.executable, "radar/agents.py", "draft"]),
    ("validate", [sys.executable, "radar/validate.py"]),
    ("critique", [sys.executable, "radar/agents.py", "critique"]),
]

MAX_REVISIONS = 2  # bounded gate-feedback revisions, then a human looks at it

def main() -> None:
    os.makedirs("artifacts", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    if os.path.exists("artifacts/critic.json"):
        os.remove("artifacts/critic.json")  # fresh run, no stale feedback
    attempts = 0
    i = 0
    while i < len(STEPS):
        name, cmd = STEPS[i]
        print(f"== {name}")
        if subprocess.run(cmd).returncode != 0:
            if name in ("validate", "critique") and attempts < MAX_REVISIONS:
                attempts += 1
                print(f"== {name} rejected draft, revision {attempts}")
                i = 1  # back to the draft step, which now sees the gate feedback
                continue
            sys.exit(f"pipeline stopped at '{name}' - nothing was published")
        i += 1
    import json
    import re

    today = datetime.date.today().isoformat()
    dest = f"output/brief-{today}.md"
    signals = json.load(open("artifacts/signals.json", encoding="utf-8"))
    body = open("artifacts/draft.md", encoding="utf-8").read()
    used = sorted({int(n) for n in re.findall(r"\[(\d+)\]", body)})
    sources = "\n".join(f"{n}. [{signals[n - 1]['title']}]({signals[n - 1]['url']})" for n in used)
    with open(dest, "w", encoding="utf-8") as out:
        out.write(f"---\ndate: {today}\npipeline: ctaio-radar\nstatus: validated\n---\n\n")
        out.write(body + f"\n\n## Sources\n{sources}\n")
    print(f"== publish\npublished {dest} with {len(used)} sources")

if __name__ == "__main__":
    main()
