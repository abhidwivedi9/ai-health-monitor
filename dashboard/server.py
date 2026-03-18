from flask import Flask, jsonify, render_template_string
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.collector import get_system_metrics
from agents.ai_analyzer import analyze

app = Flask(__name__)
_last_analysis = {}

HTML = """
<!DOCTYPE html><html><head><title>AI Health Monitor</title>
<meta http-equiv="refresh" content="30">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0f1117;color:#e2e8f0;padding:24px}
h1{font-size:22px;font-weight:600;margin-bottom:4px}
.sub{color:#64748b;font-size:13px;margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:24px}
.card{background:#1e2330;border-radius:12px;padding:20px;border:1px solid #2d3748}
.label{font-size:11px;color:#64748b;text-transform:uppercase;margin-bottom:6px}
.value{font-size:28px;font-weight:600}
.bar-wrap{background:#2d3748;border-radius:4px;height:6px;margin-top:8px}
.bar{height:6px;border-radius:4px}
.green{color:#10b981}.yellow{color:#f59e0b}.red{color:#ef4444}
.bg-green{background:#10b981}.bg-yellow{background:#f59e0b}.bg-red{background:#ef4444}
.box{background:#1e2330;border-radius:12px;padding:20px;border:1px solid #2d3748;margin-bottom:24px}
.ai-title{font-size:15px;font-weight:600;margin-bottom:12px;color:#a78bfa}
.sev{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:12px}
.sev-HEALTHY{background:#064e3b;color:#10b981}
.sev-WARNING{background:#451a03;color:#f59e0b}
.sev-CRITICAL{background:#450a0a;color:#ef4444}
.sev-UNKNOWN{background:#1e2330;color:#64748b}
.summary{font-size:14px;color:#cbd5e1;margin-bottom:16px;line-height:1.6}
.stitle{font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;margin:12px 0 6px}
ul{padding-left:16px}
ul li{font-size:13px;color:#94a3b8;margin-bottom:4px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;color:#64748b;padding:4px 8px;border-bottom:1px solid #2d3748}
td{padding:4px 8px;color:#cbd5e1;border-bottom:1px solid #1a202c}
.meta{font-size:11px;color:#475569;margin-top:16px}
</style></head><body>
<h1>AI Server Health Monitor</h1>
<div class="sub">Host: {{d.hostname}} | Uptime: {{d.uptime_hours}}h | {{d.timestamp}} | Auto-refresh: 30s</div>
<div class="grid">
  <div class="card">
    <div class="label">CPU</div>
    <div class="value {{'red' if d.cpu.overall_pct>75 else 'yellow' if d.cpu.overall_pct>50 else 'green'}}">{{d.cpu.overall_pct}}%</div>
    <div class="bar-wrap"><div class="bar {{'bg-red' if d.cpu.overall_pct>75 else 'bg-yellow' if d.cpu.overall_pct>50 else 'bg-green'}}" style="width:{{d.cpu.overall_pct}}%"></div></div>
    <div style="font-size:11px;color:#64748b;margin-top:6px">{{d.cpu.core_count}} cores @ {{d.cpu.freq_mhz}}MHz</div>
  </div>
  <div class="card">
    <div class="label">Memory</div>
    <div class="value {{'red' if d.memory.used_pct>75 else 'yellow' if d.memory.used_pct>50 else 'green'}}">{{d.memory.used_pct}}%</div>
    <div class="bar-wrap"><div class="bar {{'bg-red' if d.memory.used_pct>75 else 'bg-yellow' if d.memory.used_pct>50 else 'bg-green'}}" style="width:{{d.memory.used_pct}}%"></div></div>
    <div style="font-size:11px;color:#64748b;margin-top:6px">{{d.memory.used_gb}}GB / {{d.memory.total_gb}}GB</div>
  </div>
  <div class="card">
    <div class="label">Disk</div>
    <div class="value {{'red' if d.disk.used_pct>80 else 'yellow' if d.disk.used_pct>60 else 'green'}}">{{d.disk.used_pct}}%</div>
    <div class="bar-wrap"><div class="bar {{'bg-red' if d.disk.used_pct>80 else 'bg-yellow' if d.disk.used_pct>60 else 'bg-green'}}" style="width:{{d.disk.used_pct}}%"></div></div>
    <div style="font-size:11px;color:#64748b;margin-top:6px">{{d.disk.free_gb}}GB free</div>
  </div>
  <div class="card">
    <div class="label">Network</div>
    <div class="value green">{{d.network.bytes_recv_mb}}MB</div>
    <div style="font-size:11px;color:#64748b;margin-top:6px">Recv | Sent: {{d.network.bytes_sent_mb}}MB</div>
  </div>
</div>
{% if ai %}
<div class="box">
  <div class="ai-title">AI Analysis — {{ai.model}}</div>
  <span class="sev sev-{{ai.severity}}">{{ai.severity}}</span>
  <div class="summary">{{ai.summary}}</div>
  {% if ai.issues %}<div class="stitle">Issues</div><ul>{% for i in ai.issues %}<li>{{i}}</li>{% endfor %}</ul>{% endif %}
  {% if ai.actions %}<div class="stitle">Actions</div><ul>{% for a in ai.actions %}<li>{{a}}</li>{% endfor %}</ul>{% endif %}
  <div class="stitle">Prediction</div>
  <div style="font-size:13px;color:#94a3b8">{{ai.prediction}}</div>
  <div class="meta">Confidence: {{ai.confidence}}% | Time: {{ai.analysis_time_sec}}s</div>
</div>
{% endif %}
<div class="box">
  <div class="ai-title">Top Processes</div>
  <table><tr><th>PID</th><th>Name</th><th>CPU%</th><th>MEM%</th></tr>
  {% for p in d.top_processes %}
  <tr><td>{{p.pid}}</td><td>{{p.name}}</td>
  <td class="{{'red' if p.cpu_pct>50 else 'yellow' if p.cpu_pct>20 else 'green'}}">{{p.cpu_pct}}%</td>
  <td>{{p.mem_pct}}%</td></tr>
  {% endfor %}</table>
</div>
</body></html>"""

@app.route("/")
def dashboard():
    return render_template_string(HTML, d=get_system_metrics(), ai=_last_analysis or None)

@app.route("/api/metrics")
def api_metrics():
    return jsonify(get_system_metrics())

@app.route("/api/analyze")
def api_analyze():
    global _last_analysis
    metrics = get_system_metrics()
    _last_analysis = analyze(metrics)
    return jsonify({"metrics": metrics, "analysis": _last_analysis})

@app.route("/api/history")
def api_history():
    log_path = Path("logs/alerts.jsonl")
    if not log_path.exists():
        return jsonify([])
    records = []
    with open(log_path) as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                pass
    return jsonify(records[-50:])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
