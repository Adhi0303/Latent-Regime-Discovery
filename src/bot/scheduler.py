import schedule
import time
import requests
import os

API_URL = os.getenv("API_URL", "http://api-server:8000")

def trigger_daily_cycle():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Triggering Multi-Asset Trading Cycle...")
    try:
        response = requests.post(f"{API_URL}/api/bot/run")
        print(f"Cycle Result: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to trigger cycle: {e}")

def trigger_retrainer_heartbeat():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Triggering Auto-Retrainer Heartbeat...")
    try:
        response = requests.post(f"{API_URL}/api/bot/retrain")
        print(f"Heartbeat Result: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to trigger heartbeat: {e}")

# In production, markets close at 4:00 PM EST (21:00 UTC).
# We run the cycle at 4:15 PM EST (21:15 UTC).
schedule.every().day.at("21:15").do(trigger_daily_cycle)

# We run the Heartbeat monitor at 5:00 PM EST (22:00 UTC)
schedule.every().day.at("22:00").do(trigger_retrainer_heartbeat)

print("Autonomous Scheduler Started. Waiting for scheduled tasks...")

while True:
    schedule.run_pending()
    time.sleep(60) # Wake up every minute to check schedule
