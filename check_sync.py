import subprocess
import os

def run_command(cmd):
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except Exception as e:
        return f"Error: {e}"

def check_sync():
    print("\n" + "="*50)
    print("      🚀 SURVEILLANCE AI - TEAM SYNC CHECKER")
    print("="*50)

    # 1. Fetch latest updates from GitHub without merging
    print("\n[1/3] Fetching latest info from GitHub...")
    run_command("git fetch origin master")

    # 2. Check local vs remote status
    local_hash = run_command("git rev-parse HEAD")
    remote_hash = run_command("git rev-parse origin/master")

    if local_hash == remote_hash:
        print("✅ STATUS: Your laptop is perfectly SYNCED with GitHub.")
    else:
        print("⚠️ STATUS: GitHub has NEW changes. You should run 'git pull origin master'.")

    # 3. Show recent commit history with Authors
    print("\n[2/3] Recent Work History (Last 5 changes):")
    print("-" * 50)
    # Format: [Date] Author: Message
    history = run_command('git log -n 5 --pretty=format:"[%ad] %an: %s" --date=short origin/master')
    print(history)

    # 4. Summary of who is doing what (based on TASKS.md)
    print("\n[3/3] Current Roles (from TASKS.md):")
    print("-" * 50)
    if os.path.exists("TASKS.md"):
        with open("TASKS.md", "r") as f:
            lines = f.readlines()
            for line in lines:
                if "Person 1" in line or "Person 2" in line or "Person 3" in line:
                    print(line.strip())
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    check_sync()
