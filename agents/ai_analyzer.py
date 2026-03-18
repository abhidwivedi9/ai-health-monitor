import requests
import json
import time
from typing import Optional

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

SYSTEM_PROMPT = """You are an expert DevOps SRE AI assistant.
Analyze server health metrics and respond ONLY with a valid JSON object with these keys:
- severity: HEALTHY | WARNING | CRITICAL
- summary: one sentence description
- issues: list of detected issues
- actions: list of recommended actions
- prediction: what happens in 30 mins if no action
- confidence: score 0-100"""

def build_prompt(metrics):
    return f"""Analyze this server:
HOST: {metrics['hostname']} | Uptime: {metrics['uptime_hours']}h
CPU: {metrics['cpu']['overall_pct']}% | Memory: {metrics['memory']['used_pct']}% | Disk: {metrics['disk']['used_pct']}%
Top processes: {json.dumps(metrics['top_processes'])}
Respond ONLY with valid JSON. No extra text."""

def query_ollama(prompt, retries=3):
    payload = {"model": MODEL, "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
               "stream": False, "options": {"temperature": 0.2, "num_predict": 512}}
    for attempt in range(retries):
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=60)
            r.raise_for_status()
            return r.json().get("response", "")
        except requests.exceptions.ConnectionError:
            print("  [!] Ollama not running. Run: ollama serve")
            time.sleep(2)
        except Exception as e:
            print(f"  [!] Error: {e}")
            break
    return None

def parse_ai_response(raw):
    if not raw:
        return {"severity":"UNKNOWN","summary":"AI unavailable","issues":[],
                "actions":["Run: ollama serve"],"prediction":"N/A","confidence":0}
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
        clean = clean.strip()
    try:
        parsed = json.loads(clean)
        parsed.setdefault("severity","UNKNOWN")
        parsed.setdefault("summary","Analysis done")
        parsed.setdefault("issues",[])
        parsed.setdefault("actions",[])
        parsed.setdefault("prediction","Unknown")
        parsed.setdefault("confidence",0)
        return parsed
    except Exception:
        start, end = raw.find('{'), raw.rfind('}')+1
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end])
            except Exception:
                pass
    return {"severity":"UNKNOWN","summary":"Could not parse response",
            "issues":[],"actions":[],"prediction":"N/A","confidence":0}

def analyze(metrics):
    print(f"  [*] Sending to Ollama ({MODEL})...")
    start = time.time()
    result = parse_ai_response(query_ollama(build_prompt(metrics)))
    result["analysis_time_sec"] = round(time.time()-start, 1)
    result["model"] = MODEL
    print(f"  [+] Done in {result['analysis_time_sec']}s — {result['severity']}")
    return result

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '..')
    from app.collector import get_system_metrics
    print(json.dumps(analyze(get_system_metrics()), indent=2))
