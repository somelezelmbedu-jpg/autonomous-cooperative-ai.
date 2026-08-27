# Autonomous Cooperative AI — Scaffold

This implements a constitution-checked autonomous AI architecture:

Goal Manager -> Reasoning Engine -> Simulation (risk estimate) -> Safety and Constitutional Guard -> Execute (if allowed) or Escalate to human

Every proposed action is checked against a constitution before it runs.
Irreversible, self-modifying, or personal-data-touching actions are
automatically held for human review. Every step is written to a
tamper-evident audit log.

## Running it locally

pip install -r requirements.txt

python main.py

python app.py

Optional: set ANTHROPIC_API_KEY as an environment variable to let the
Reasoning Engine use Claude for planning instead of the built-in
rule-based fallback.
