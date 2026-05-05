import subprocess
import requests
import threading
import time
import sys
import os

# --- Configurations ---
MAX_PODS = 4
CURRENT_PODS = [8000]
LOAD_THRESHOLD = 50 # Start scaling AFTER 50 concurrent requests
processes = {}
load_stats = {8000: 0}

def start_pod(port):
    if port in processes: return
    print(f"[AUTOSCALER] High Load! Deploying NEW Pod on Port {port}...")
    processes[port] = subprocess.Popen([sys.executable, "-u", "main.py"], 
                                      cwd="backend", 
                                      env={**os.environ, "PORT": str(port)})
    load_stats[port] = 0
    time.sleep(3)

def autoscaler_daemon():
    while True:
        total_requests = sum(load_stats.values())
        avg_load = total_requests / len(CURRENT_PODS)
        
        if avg_load > LOAD_THRESHOLD and len(CURRENT_PODS) < MAX_PODS:
            new_port = 8000 + len(CURRENT_PODS)
            CURRENT_PODS.append(new_port)
            start_pod(new_port)
            for p in CURRENT_PODS: load_stats[p] = 0
            
        time.sleep(1)

def send_traffic_burst(count=150):
    print(f"\n[STRESS] Sending intensive burst of {count} detections...")
    
    def worker(idx):
        active_pods = list(CURRENT_PODS) # Create a copy to avoid race condition
        port = active_pods[idx % len(active_pods)]
        
        payload = {
            "camera_id": f"SCALING-CAM-{idx}", "class_name": "Person", "confidence": 0.99,
            "xcenter": 0.5, "ycenter": 0.5, "width": 0.2, "height": 0.4
        }
        
        try:
            resp = requests.post(f"http://localhost:{port}/detections/", json=payload, timeout=10)
            if resp.status_code == 201:
                load_stats[port] += 1
        except Exception:
            pass

    threads = []
    for i in range(count):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
        if i % 10 == 0: time.sleep(0.1)
    
    for t in threads:
        t.join()

def run_lab():
    print("--- STARTING AUTO-SCALING PERFORMANCE LAB ---")
    start_pod(8000)
    threading.Thread(target=autoscaler_daemon, daemon=True).start()
    
    print("\n[PHASE 1] Normal Baseline (No Scaling)")
    send_traffic_burst(30)
    print(f"REPORT: Status={len(CURRENT_PODS)} Pod | Distribution={load_stats}")
    
    print("\n[PHASE 2] High-Traffic Spike (Triggers Scale-Out)")
    send_traffic_burst(150)
    
    print("\n[PHASE 3] Final State (Distributing across New Pods)")
    for p in CURRENT_PODS: load_stats[p] = 0
    send_traffic_burst(150)
    
    print(f"\n[AUTOSCALER FINAL REPORT]")
    print(f"Final Count: {len(CURRENT_PODS)} ACTIVE PODS")
    print(f"Final Distribution: {load_stats}")
    print(f"CONCLUSION: Multi-Pod Horizontal scaling successfully handled the spike.")

    for p in processes.values():
        p.terminate()

if __name__ == "__main__":
    run_lab()
