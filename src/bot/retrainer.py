import os
import sys
import sqlite3
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.models.hmm_regimes import run_hmm_pipeline as train_hmm
from src.models.train_lstm import train_lstm

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'trading_bot.db'))
TICKERS = ["^GSPC", "NVDA", "TSLA", "BTC-USD", "BRK-B"]

ERROR_THRESHOLD_PCT = 5.0
LOOKBACK_DAYS = 7

def check_and_retrain():
    """
    Heartbeat Monitor: Checks the rolling 7-day MAE for all tickers.
    Triggers retraining if MAE > 5% or if it's the 1st of the month.
    """
    print("\n--- Running Auto-Retrainer Heartbeat Check ---")
    
    if not os.path.exists(DB_PATH):
        print("Database not found. Skipping retrainer check.")
        return {"status": "skipped", "reason": "No database found."}
        
    today = datetime.datetime.now()
    is_first_of_month = (today.day == 1)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    retrained_tickers = []
    
    for ticker in TICKERS:
        cursor.execute('''
            SELECT error_pct FROM predictions 
            WHERE ticker = ? AND error_pct IS NOT NULL 
            ORDER BY timestamp DESC LIMIT ?
        ''', (ticker, LOOKBACK_DAYS))
        
        rows = cursor.fetchall()
        
        # If we don't have enough data yet, skip error check but allow 1st of month
        if len(rows) > 0:
            avg_error = sum([r[0] for r in rows]) / len(rows)
        else:
            avg_error = 0.0
            
        print(f"Ticker: {ticker} | 7-Day Rolling MAE: {avg_error:.2f}%")
        
        needs_retraining = False
        trigger_reason = ""
        
        if is_first_of_month:
            needs_retraining = True
            trigger_reason = "1st of the Month Routine Schedule"
        elif avg_error > ERROR_THRESHOLD_PCT:
            needs_retraining = True
            trigger_reason = f"Emergency: Rolling MAE exceeded threshold ({avg_error:.2f}% > {ERROR_THRESHOLD_PCT}%)"
            
        if needs_retraining:
            print(f"  [!] Trigger Fired: {trigger_reason}")
            print(f"  [!] Retraining models for {ticker}...")
            
            try:
                # 1. Retrain HMM Macro Model
                train_hmm(ticker)
                
                # 2. Retrain LSTM Neural Network
                train_lstm(ticker, epochs=30) # Use 30 epochs for routine catch-up
                
                retrained_tickers.append({
                    "ticker": ticker,
                    "reason": trigger_reason,
                    "previous_error": avg_error
                })
                print(f"  [+] Retraining complete for {ticker}.")
            except Exception as e:
                print(f"  [-] Failed to retrain {ticker}: {e}")
                
    conn.close()
    
    if len(retrained_tickers) == 0:
        print("No retraining required today. Models are healthy.")
        return {"status": "healthy", "message": "All models healthy, no retraining needed."}
    else:
        return {"status": "retrained", "models_updated": retrained_tickers}

if __name__ == "__main__":
    check_and_retrain()
