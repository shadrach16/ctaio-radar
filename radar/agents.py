"""Steps 2 and 4 - the two agents, run through Claude Code headless.

Two distinct agents with different jobs and different incentives:
  - drafter: writes an article brief from signals.json
  - critic:  tries to refute the draft against signals.json, fails closed

Using `claude -p` as the agent engine is deliberate: this artifact is for
ctaio.dev, whose whole subject is Claude Code workflows.
"""
import json
import subprocess
import sys

# Both agents ended up on sonnet. We started the critic on haiku (cheap
# refutation pass) but it ignored the role contract entirely and answered
# conversationally - a weekly pipeline earns the stronger model on every
# judgement step. Haiku stays viable only for extraction-shaped steps.
DRAFT_MODEL = "claude-sonnet-5"
CRITIC_MODEL = "claude-sonnet-5"

DRAFTER = """You are a pure text function: read stdin, reply with the finished
brief as your message text. You have no tools. Never write files, never ask
permission, never describe what you would do - output the brief itself.
You draft article briefs for ctaio.dev, a site for practitioners of agentic
AI coding. House style: plain prose, heavy on craft, low on hype, no emojis.
The sources arrive as a NUMBERED list. Cite by writing the bare marker [n]
immediately after each claim, using only numbers from the list. Do not write
URLs yourself - the publisher expands markers. A claim without a marker is
forbidden. Produce markdown: a # title, a 2-sentence angle, then a 5-bullet
outline where every bullet ends with its [n] marker. Nothing else.
Format example (follow the shape exactly, not the content):
# Agents Meet the Debugger
Two sentences of angle text here. Second sentence here. [2]
- First outline bullet making one sourced point [1]
- Second bullet [4]"""

CRITIC = """You are a pure text function with no tools: read stdin, reply with
json only. You are the fact gate for ctaio.dev. You receive SOURCES (json)
and a DRAFT. Your job is to refute the draft: find claims not supported by
the sources, cited URLs that are not in the sources, and hype language.
Reply with ONLY json: {"verdict": "pass"|"fail", "reasons": ["..."]}.
When in doubt, fail."""

def run_agent(system_prompt: str, payload: str, model: str) -> str:
    proc = subprocess.run(
        ["claude", "-p", "--model", model, "--append-system-prompt", system_prompt],
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
        shell=True,
    )
    if proc.returncode != 0:
        sys.exit(f"agent failed: {proc.stderr[:400]}")
    out = proc.stdout.strip()
    lowered = out.lower()
    if "permission" in lowered or "should i proceed" in lowered:
        sys.exit("agent tried to act interactively instead of returning text - aborting")
    return out

def draft() -> None:
    signals = json.load(open("artifacts/signals.json", encoding="utf-8"))
    numbered = "\n".join(
        f"{i + 1}. {s['title']} ({s['points']} pts) - {s['url']}"
        for i, s in enumerate(signals)
    )
    payload = f"SOURCES:\n{numbered}\n\nWrite this week's brief."
    try:
        reasons = json.load(open("artifacts/critic.json", encoding="utf-8")).get("reasons")
        if reasons:
            payload += (
                "\n\nYour previous draft was rejected by the fact gate for the"
                " reasons below. Revise: claim only what the source titles"
                " literally support.\n- " + "\n- ".join(reasons)
            )
            print("drafter: revising against critic feedback")
    except FileNotFoundError:
        pass
    out = run_agent(DRAFTER, payload, DRAFT_MODEL)
    with open("artifacts/draft.md", "w", encoding="utf-8") as f:
        f.write(out)
    print(f"drafter: {len(out.split())} words -> artifacts/draft.md")

def critique() -> None:
    signals = open("artifacts/signals.json", encoding="utf-8").read()
    the_draft = open("artifacts/draft.md", encoding="utf-8").read()
    out = run_agent(CRITIC, f"SOURCES:\n{signals}\n\nDRAFT:\n{the_draft}", CRITIC_MODEL)
    start, end = out.find("{"), out.rfind("}")
    try:
        verdict = json.loads(out[start : end + 1])
    except (ValueError, IndexError):
        verdict = {"verdict": "fail", "reasons": ["critic output was not json - failing closed"]}
    with open("artifacts/critic.json", "w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=2)
    print(f"critic: {verdict['verdict']} -> artifacts/critic.json")
    if verdict["verdict"] != "pass":
        sys.exit("critic: draft rejected:\n- " + "\n- ".join(verdict.get("reasons", [])))

if __name__ == "__main__":
    {"draft": draft, "critique": critique}[sys.argv[1]]()
