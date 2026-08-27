# ctaio-radar

A content radar for ctaio.dev: collect -> draft (agent) -> validate (deterministic) -> critique (agent) -> publish, with a bounded gate-feedback revision loop. Uses Claude Code headless (`claude -p`) as the agent engine. Built as a 40-minute assessment artifact for We The Flywheel.

Run: `python run.py` (needs Python 3.10+ and an authenticated Claude Code CLI; the HN collector needs no key).

Design choices worth reading: the citation contract is structural ([n] markers mapped by code, not prompt-and-hope), cheap deterministic checks run before expensive LLM judgement, and every gate failure feeds back into one bounded revision - after that a human looks.
