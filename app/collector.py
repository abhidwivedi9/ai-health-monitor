import psutil
import socket
import datetime
import json
import time
import platform

def get_system_metrics():
    cpu_per_core = psutil.cpu_percent(percpu=True, interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime_seconds = (datetime.datetime.now() - boot_time).total_seconds()
    processes = []
    for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                       key=lambda p: p.info['cpu_percent'] or 0, reverse=True)[:5]:
        try:
            processes.append({"pid": proc.info['pid'], "name": proc.info['name'],
                "cpu_pct": round(proc.info['cpu_percent'] or 0, 1),
                "mem_pct": round(proc.info['memory_percent'] or 0, 1)})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "cpu": {"overall_pct": psutil.cpu_percent(interval=0.1),
            "per_core": cpu_per_core, "core_count": psutil.cpu_count(),
            "freq_mhz": round(psutil.cpu_freq().current) if psutil.cpu_freq() else 0,
            "load_avg": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0,0,0]},
        "memory": {"total_gb": round(mem.total/(1024**3),1),
            "used_gb": round(mem.used/(1024**3),1),
            "available_gb": round(mem.available/(1024**3),1), "used_pct": mem.percent},
        "disk": {"total_gb": round(disk.total/(1024**3),1),
            "used_gb": round(disk.used/(1024**3),1),
            "free_gb": round(disk.free/(1024**3),1), "used_pct": disk.percent},
        "network": {"bytes_sent_mb": round(net.bytes_sent/(1024**2),1),
            "bytes_recv_mb": round(net.bytes_recv/(1024**2),1),
            "packets_sent": net.packets_sent, "packets_recv": net.packets_recv},
        "uptime_hours": round(uptime_seconds/3600,1),
        "top_processes": processes
    }

def determine_severity(metrics):
    cpu = metrics["cpu"]["overall_pct"]
    mem = metrics["memory"]["used_pct"]
    disk = metrics["disk"]["used_pct"]
    if cpu > 90 or mem > 90 or disk > 90:
        return "CRITICAL"
    elif cpu > 75 or mem > 75 or disk > 80:
        return "WARNING"
    return "HEALTHY"

if __name__ == "__main__":
    print(json.dumps(get_system_metrics(), indent=2))
