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
    # Daily Trading: Run the bot every weekday at 21:30 UTC (After Market Close)
    schedule.every().monday.at("21:30").do(trigger_daily_cycle)
    schedule.every().tuesday.at("21:30").do(trigger_daily_cycle)
    schedule.every().wednesday.at("21:30").do(trigger_daily_cycle)
    schedule.every().thursday.at("21:30").do(trigger_daily_cycle)
    schedule.every().friday.at("21:30").do(trigger_daily_cycle)

    # Weekly Continuous Learning: Run at 22:00 UTC on Friday
    schedule.every().friday.at("22:00").do(trigger_continuous_learning)

    # Weekly Macro Retrainer Heartbeat: Check if a full retrain is needed
    schedule.every().sunday.at("00:00").do(trigger_retrainer_heartbeat)

    print("Daily Trading & Weekly Learning Scheduler Setup Complete.")
