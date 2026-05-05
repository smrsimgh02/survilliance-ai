import subprocess
import time
import os
import sys
from dotenv import load_dotenv

# Load root .env
load_dotenv()

def run_live_system():
    print("=" * 55)
    print("   SURVEILLANCE AI - LIVE SYSTEM LAUNCHER")
    print("=" * 55)
    print()

    processes = []

    # Step 1: Start Backend Hub
    print("[1/2] Starting Backend Hub (FastAPI)...")
    hub = subprocess.Popen(
        [sys.executable, "-u", "main.py"],
        cwd="backend",
        env={**os.environ, "PORT": "8001"}
    )
    processes.append(hub)
    time.sleep(4)
    print("[1/2] [OK] Backend Hub running at http://localhost:8001")
    print("[1/2] Dashboard: http://localhost:8001/monitor/index.html")

    # Step 2: Start AI Node (will ask for mobile IP)
    print()
    print("[2/2] Starting AI Detection Node...")
    print("-" * 55)
    ai = subprocess.Popen(
        [sys.executable, "-u", "proper_yolo_node.py"],
        cwd="ai_node",
        env=os.environ
    )
    processes.append(ai)

    print()
    print("=" * 55)
    print("  SYSTEM LIVE - Press Ctrl+C to stop everything")
    print("=" * 55)

    try:
        while True:
            for p in processes:
                if p.poll() is not None:
                    print("[ALERT] A component crashed!")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nShutting down all components...")
        for p in processes:
            p.terminate()
        print("System stopped.")

if __name__ == "__main__":
    run_live_system()
