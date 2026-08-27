# ctaio-radar

A weekly content radar for [ctaio.dev](https://ctaio.dev): it collects the week's
agentic-coding signals from Hacker News, has one agent draft a sourced article
brief, forces that draft through two gates that fail closed, and only then
publishes. Claude Code headless (`claude -p`) is the agent engine — a pipeline
about agentic coding, run by the tool it covers.

```
collect ──▶ draft ──▶ validate ──▶ critique ──▶ publish
(python)   (agent)  (deterministic)  (agent)    (python)
              ▲                          │
              └── bounded revision ◀─────┘
                  (gate feedback, max 2)
```

A real run's output is committed: [`output/brief-2026-08-27.md`](output/brief-2026-08-27.md),
published only after both gates passed, with every citation mapped to a
collected source.

## How it works

| Step | File | What it does |
|---|---|---|
| collect | `radar/collect.py` | Pulls a week of HN stories for four agentic-coding queries (Algolia API, no key), dedupes, and refuses to continue with fewer than 3 signals. Writes `artifacts/signals.json` — the **single source of truth** later steps may cite. |
| draft | `radar/agents.py draft` | `claude -p --model claude-sonnet-5` with a pure-function system prompt. Input: the numbered source list. Output: a brief carrying bare `[n]` citation markers only. |
| validate | `radar/validate.py` | Deterministic, runs **before** any expensive judgement: hype-vocabulary scan, marker-range checks, minimum three citations, rejects raw URLs the agent wrote itself. |
| critique | `radar/agents.py critique` | A second agent whose only job is refutation against `signals.json`. Non-JSON output fails closed. |
| publish | `run.py` | Expands `[n]` markers into markdown links **by code** and writes `output/brief-DATE.md`. Any gate failure feeds its reasons back to the draft step for a bounded revision (max 2) — after that, a human looks. |

## Design choices that came from failures, not foresight

This was built in a 40-minute timed exercise, and it broke three different
ways before the first clean run. The fixes are the design:

1. **Headless agents must be pure functions.** The first drafter run answered
   like an interactive session and *asked permission to write files* instead of
   returning text. Fix: a pure-function contract in the system prompt plus a
   guard that aborts on permission-seeking output.
2. **Citation compliance is structural, not prompted.** Haiku ignored a
   `[source](url)` citation rule through two prompt iterations. Fix: stop
   prompt-and-hoping — numbered sources in, bare `[n]` markers out, and
   deterministic code does the URL mapping. Judgement steps moved to Sonnet;
   the cheap model had been on the wrong step.
3. **Gates share one feedback channel.** The critic correctly caught the
   drafter inflating "used Codex more than Claude Code" into "Codex ahead."
   The revision fixed that — then quoted an HN title containing "insane" and
   tripped the hype gate, which had no retry path. Fix: both gates write to
   the same feedback file and the orchestrator routes any rejection back to
   the drafter, bounded.

The commit history shows the sequence honestly.

## Run it

```bash
python run.py
```

Requirements: Python 3.10+, an authenticated [Claude Code](https://claude.com/claude-code)
CLI on PATH. The collector needs no API key. Per-step artifacts land in
`artifacts/` (gitignored); published briefs land in `output/`.

## Provenance

Built by [Tunde Oluwamo](https://github.com/shadrach16) with Claude Code as a
timed hiring-assessment artifact for We The Flywheel, August 2026.
