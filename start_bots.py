import subprocess
import sys
import time
import os

# List of bot scripts to run
bots = [
    "mod_bot.py",
    "shop.py",
    "main.py",
    "prof.py"
]

processes = []

def start_bots():
    print(f"🚀 Starting {len(bots)} bots...")
    
    for script in bots:
        if not os.path.exists(script):
            print(f"❌ File not found: {script}")
            continue
            
        print(f"▶️ Launching {script}...")
        # Use sys.executable to ensure we use the same python interpreter
        p = subprocess.Popen([sys.executable, script])
        processes.append((script, p))
        
    print("✅ All bots launched!")
    print("Press Ctrl+C to stop all bots.")

    try:
        # Monitor processes
        while True:
            time.sleep(1)
            for script, p in processes:
                if p.poll() is not None:
                    print(f"⚠️ {script} stopped! Restarting...")
                    # Restart the process
                    new_p = subprocess.Popen([sys.executable, script])
                    processes.remove((script, p))
                    processes.append((script, new_p))
                    
    except KeyboardInterrupt:
        print("\n🛑 Stopping all bots...")
        for script, p in processes:
            p.terminate()
        sys.exit(0)

if __name__ == "__main__":
    start_bots()
