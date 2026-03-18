#!/usr/bin/env python3
import time
import argparse
import threading
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.collector import get_system_metrics, determine_severity
from agents.ai_analyzer import analyze
from agents.alert_manager import dispatch

def monitor_loop(interval=60, ai_every=3):
    print(f"""
╔══════════════════════════════════════════╗
║   AI-Powered Server Health Monitor       ║
║   Interval: {interval}s  AI every: {ai_every} cycles       ║
║   Dashboard: http://localhost:8080        ║
║   Press Ctrl+C to stop                   ║
╚══════════════════════════════════════════╝
""")
    cycle = 0
    previous_severity = None
    last_analysis = {}
    while True:
        cycle += 1
        print(f"\n[Cycle {cycle}] Collecting metrics...")
        try:
            metrics = get_system_metrics()
            rule_severity = determine_severity(metrics)
            if cycle % ai_every == 0 or cycle == 1:
                analysis = analyze(metrics)
            else:
                analysis = dict(last_analysis) if last_analysis else {
                    "severity": rule_severity,
                    "summary": f"Rule-based: {rule_severity}. AI runs every {ai_every} cycles.",
                    "issues": [], "actions": [], "prediction": "N/A",
                    "confidence": 0, "model": "rule-based", "analysis_time_sec": 0}
            last_analysis = analysis
            dispatch(metrics, analysis, previous_severity)
            previous_severity = analysis["severity"]
        except KeyboardInterrupt:
            print("\n[*] Stopped. Goodbye!\n")
            break
        except Exception as e:
            print(f"  [!] Error: {e}")
        print(f"  [*] Next check in {interval}s...")
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[*] Stopped. Goodbye!\n")
            break

def start_dashboard():
    from dashboard.server import app
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

def main():
    parser = argparse.ArgumentParser(description="AI Server Health Monitor")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--ai-every", type=int, default=3)
    parser.add_argument("--no-dashboard", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.once:
        metrics = get_system_metrics()
        analysis = analyze(metrics)
        dispatch(metrics, analysis)
        return
    if not args.no_dashboard:
        print("[*] Starting dashboard at http://localhost:8080 ...")
        threading.Thread(target=start_dashboard, daemon=True).start()
    monitor_loop(interval=args.interval, ai_every=args.ai_every)

if __name__ == "__main__":
    main()
