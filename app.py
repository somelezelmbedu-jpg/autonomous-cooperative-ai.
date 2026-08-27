"""
Minimal web UI so this can run as a hosted app (Render/Replit/etc.)
instead of only a CLI demo.
"""

from flask import Flask, request, jsonify, render_template_string
from main import AutonomousSystem

app = Flask(__name__)
system = AutonomousSystem()

PAGE = """
<!doctype html>
<title>Autonomous Cooperative AI — Demo</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; }
  textarea { width: 100%; height: 70px; }
  button { padding: 8px 16px; margin-top: 8px; }
  .card { border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-top: 10px; }
  .allow { border-left: 4px solid #2a2; }
  .escalate { border-left: 4px solid #c90; }
  .block { border-left: 4px solid #c22; }
  pre { white-space: pre-wrap; }
</style>
<h2>Autonomous Cooperative AI — Demo</h2>
<p>Enter a goal. Every proposed action is checked against the constitution before it "executes."</p>
<form method="post">
  <textarea name="goal" placeholder="e.g. Summarize this week's notes">{{ goal or '' }}</textarea><br>
  <button type="submit">Submit goal</button>
</form>
{% if results %}
  <h3>Results</h3>
  {% for r in results %}
    <div class="card {{ r.verdict }}">
      <b>{{ r.action_type }}</b> — {{ r.description }}<br>
      Verdict: <b>{{ r.verdict }}</b> | Risk score: {{ r.risk.risk_score }}<br>
      Result: {{ r.result }}
    </div>
  {% endfor %}
{% endif %}
<hr>
<p><a href="/audit">View audit log</a></p>
"""

AUDIT_PAGE = """
<!doctype html>
<title>Audit Log</title>
<body style="font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto;">
<h2>Audit Log</h2>
<p>Chain intact: <b>{{ intact }}</b></p>
<pre>{{ entries }}</pre>
<a href="/">Back</a>
</body>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    results, goal = None, None
    if request.method == "POST":
        goal = request.form.get("goal", "").strip()
        if goal:
            out = system.pursue_goal(goal, submitted_by="web_user")
            results = out["results"]
    return render_template_string(PAGE, results=results, goal=goal)


@app.route("/audit")
def audit():
    entries = system.audit_log.read_all()
    import json
    pretty = "\n\n".join(json.dumps(e, indent=2) for e in entries[-20:])
    return render_template_string(AUDIT_PAGE, intact=system.audit_log.verify_chain(), entries=pretty)


@app.route("/api/goal", methods=["POST"])
def api_goal():
    data = request.get_json(force=True)
    out = system.pursue_goal(data.get("goal", ""), submitted_by=data.get("submitted_by", "api"))
    return jsonify(out)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
