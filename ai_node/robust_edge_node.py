import requests
import sqlite3
import time
import json
import os
import random
import threading

# --- Configurations ---
FOG_HUB_URL = "http://localhost:8000/detections/"
DB_PATH = "edge_buffer.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS buffer 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  payload TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_to_buffer(payload):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO buffer (payload) VALUES (?)", (json.dumps(payload),))
    conn.commit()
    conn.close()
    print(f"[LOCAL BUFFER] Saved offline detection")

def get_buffer_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM buffer")
    count = c.fetchone()[0]
    conn.close()
    return count

def drain_buffer():
    while True:
        count = get_buffer_count()
        if count > 0:
            print(f"[RECOVERY] Attempting to drain {count} records...")
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, payload FROM buffer LIMIT 10")
            rows = c.fetchall()
            for row in rows:
                try:
                    resp = requests.post(FOG_HUB_URL, json=json.loads(row[1]), timeout=5)
                    if resp.status_code in [200, 201]:
                        c.execute("DELETE FROM buffer WHERE id = ?", (row[0],))
                        conn.commit()
                        print(f"[RECOVERY] Synced record {row[0]}")
                    else: break
                except: break
            conn.close()
        time.sleep(10)

def simulate_detection():
    init_db()
    threading.Thread(target=drain_buffer, daemon=True).start()
    classes = ["Person", "Vehicle", "Safety-Vest", "Helmet"]
    while True:
        obj = random.choice(classes)
        conf = round(random.uniform(0.7, 0.99), 2)
        payload = {
            "camera_id": f"EDGE-NODE-{os.getpid()}",
            "class_name": obj,
            "confidence": conf,
            "xcenter": 0.5, "ycenter": 0.5, "width": 0.2, "height": 0.4
        }
        try:
            print(f"[LIVE] Detected {obj} ({conf*100}%)")
            resp = requests.post(FOG_HUB_URL, json=payload, timeout=2)
            if resp.status_code not in [200, 201]:
                save_to_buffer(payload)
        except Exception:
            save_to_buffer(payload)
        time.sleep(3)

if __name__ == "__main__":
    print("Starting Robust Edge Node with Store-and-Forward Support...")
    simulate_detection()
