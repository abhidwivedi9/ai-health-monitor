import json
import os
import datetime
from pathlib import Path

ALERT_LOG = Path("logs/alerts.jsonl")
SEVERITY_EMOJI = {"HEALTHY":"✅","WARNING":"⚠️","CRITICAL":"🚨","UNKNOWN":"❓"}

def log_to_file(metrics, analysis):
    ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": metrics["timestamp"],
        "hostname": metrics["hostname"],
        "cpu_pct": metrics["cpu"]["overall_pct"],
        "mem_pct": metrics["memory"]["used_pct"],
        "disk_pct": metrics["disk"]["used_pct"],
        "severity": analysis["severity"],
        "summary": analysis["summary"],
        "issues": analysis["issues"],
        "actions": analysis["actions"]
    }
    with open(ALERT_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")

def print_alert(metrics, analysis):
    sev = analysis["severity"]
    emoji = SEVERITY_EMOJI.get(sev, "?")
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*60}")
    print(f"  {emoji}  [{ts}]  {sev}  —  {metrics['hostname']}")
    print(f"{'='*60}")
    print(f"  CPU:  {metrics['cpu']['overall_pct']}%   MEM: {metrics['memory']['used_pct']}%   DISK: {metrics['disk']['used_pct']}%")
    print(f"\n  AI Summary: {analysis['summary']}")
    if analysis["issues"]:
        print(f"\n  Issues:")
        for i, issue in enumerate(analysis["issues"], 1):
            print(f"    {i}. {issue}")
    if analysis["actions"]:
        print(f"\n  Actions:")
        for i, action in enumerate(analysis["actions"], 1):
            print(f"    {i}. {action}")
    if analysis.get("prediction"):
        print(f"\n  Prediction: {analysis['prediction']}")
    print(f"\n  Model: {analysis.get('model','?')} | Confidence: {analysis.get('confidence',0)}% | Time: {analysis.get('analysis_time_sec',0)}s")
    print(f"{'='*60}\n")

def dispatch(metrics, analysis, previous_severity=None):
    log_to_file(metrics, analysis)
    print_alert(metrics, analysis)
