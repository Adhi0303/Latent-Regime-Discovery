import schedule
import time
import requests
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:7860")

def trigger_daily_cycle():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Triggering Multi-Asset Trading Cycle...")
    try:
        response = requests.post(f"{API_URL}/api/bot/run", timeout=10)
        print(f"Cycle Result: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to trigger cycle: {e}")

def trigger_retrainer_heartbeat():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Triggering Auto-Retrainer Heartbeat...")
    try:
        response = requests.post(f"{API_URL}/api/bot/retrain", timeout=300)
        print(f"Heartbeat Result: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to trigger heartbeat: {e}")

def trigger_continuous_learning():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Triggering Continuous Learning Fine-Tuning...")
    try:
        response = requests.post(f"{API_URL}/api/bot/continuous_learn", timeout=300)
        print(f"Learning Result: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to trigger learning: {e}")

def setup_scheduler():
    # Intraday Trading: Run the bot every 1 hour
    schedule.every(1).hours.do(trigger_daily_cycle)

    # End-Of-Day Continuous Learning: Run at 4:30 PM EST (21:30 UTC)
    schedule.every().day.at("21:30").do(trigger_continuous_learning)

    # Weekly Macro Retrainer Heartbeat: Check if a full retrain is needed
    schedule.every().sunday.at("00:00").do(trigger_retrainer_heartbeat)

    print("Intraday & Continuous Learning Scheduler Setup Complete.")
