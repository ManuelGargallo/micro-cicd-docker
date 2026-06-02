import os
import time
import signal
import sys

# Configuration from environment or defaults
APP_NAME = os.getenv("APP_NAME", "MicroApp")
INTERVAL = int(os.getenv("INTERVAL", "5"))

def signal_handler(sig, frame):
    print(f"\n[{APP_NAME}] Received shutdown signal. Exiting gracefully...")
    sys.exit(0)

# Register signals for clean container termination
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    print(f"--- {APP_NAME} v1.0 Initialized ---")
    print(f"Process ID: {os.getpid()}")
    print(f"Monitoring interval: {INTERVAL}s")
    
    try:
        while True:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] {APP_NAME} is healthy. Heartbeat active.")
            time.sleep(INTERVAL)
    except Exception as e:
        print(f"Critical failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
