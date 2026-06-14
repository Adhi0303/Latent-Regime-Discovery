import os
import sys
import pandas as pd
import numpy as np
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.bot.database import init_db, log_trade, log_prediction, update_actual_price

def seed_database(ticker="^GSPC", days=30):
    init_db()
    
    safe_ticker = ticker.replace("-", "_")
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', safe_ticker))
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', safe_ticker))
    
    scaler = joblib.load(os.path.join(models_dir, "robust_scaler.pkl"))
    pca = joblib.load(os.path.join(models_dir, "pca_robust.pkl"))
    hmm = joblib.load(os.path.join(models_dir, "hmm_model.pkl"))
    
    df = pd.read_csv(os.path.join(data_dir, "features.csv"), index_col='Date', parse_dates=True)
    
    feature_cols = ['Log_Return', 'Volatility_21d', 'Momentum_21d', 'MA_Dist_50d', 'Drawdown_252d', 'Volume_Ratio_21d']
    X = df[feature_cols].copy()
    X.ffill(inplace=True)
    X.fillna(0, inplace=True)
    
    X_scaled = scaler.transform(X)
    X_pca = pca.transform(X_scaled)
    
    raw_regime_seq = hmm.predict(X_pca)
    label_map = hmm.label_map_
    df['Regime'] = np.array([label_map[l] for l in raw_regime_seq])
    
    recent_df = df.tail(days + 1)
    
    cash = 100000.0
    asset = 0.0
    
    print(f"Seeding last {days} days for {ticker}...")
    
    for i in range(1, len(recent_df)):
        date_str = recent_df.index[i].strftime('%Y-%m-%d')
        today_close = float(recent_df['Close'].iloc[i])
        
        # Simulate prediction made yesterday for today
        # Just add a small random error (e.g. -2% to +2%) to make it look realistic
        error_factor = 1.0 + np.random.uniform(-0.02, 0.02)
        predicted_close = today_close * error_factor
        
        log_prediction(ticker, predicted_close, override_date=date_str)
        update_actual_price(ticker, today_close, override_date=date_str)
        
        # Trading Logic: Based on yesterday's regime
        prev_regime = recent_df['Regime'].iloc[i-1]
        
        action = "HOLD"
        
        if prev_regime == 2: # Bear Market -> Sell
            if asset > 0:
                cash += asset * today_close
                asset = 0.0
                action = "SELL"
        else: # Bull / Sideways -> Buy
            if cash > 0:
                # Buy as much as possible
                asset += cash / today_close
                cash = 0.0
                action = "BUY"
                
        total_value = cash + (asset * today_close)
        
        # Log trade if action changed, or just log daily balance
        # For ledger we want to log every day's snapshot
        log_trade(
            ticker=ticker,
            action=action,
            amount=asset,
            price=today_close,
            cash_balance=cash,
            asset_balance=asset,
            total_value=total_value,
            override_date=date_str
        )
        
    print(f"Seeding complete! Final Portfolio Value: ${total_value:.2f}")

if __name__ == "__main__":
    seed_database("^GSPC")
    seed_database("NVDA")
    seed_database("TSLA")
