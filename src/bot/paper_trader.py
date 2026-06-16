import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
import requests

yf_session = requests.Session()
yf_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
})

import torch
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.bot.database import update_actual_price, log_prediction, log_trade, get_portfolio_state, update_portfolio, init_db
from src.features.engineering import engineer_features_df
from src.models.train_lstm import LSTMForecast

TICKERS = ["^GSPC", "NVDA", "TSLA", "BTC-USD", "BRK-B"]

def run_multi_asset_cycle():
    print("\n--- Running Multi-Asset Daily Cycle ---")
    
    init_db()
    cash, holdings = get_portfolio_state()
    
    current_prices = {}
    current_regimes = {}
    
    total_portfolio_value = cash
    
    # --- 1. Fetch Data, Evaluate Predictions & Detect Regimes ---
    for ticker in TICKERS:
        safe_ticker = ticker.replace("-", "_")
        models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', safe_ticker))
        
        # Skip if models don't exist yet
        if not os.path.exists(models_dir):
            continue
            
        try:
            features_df = None
            try:
                raw_df = yf.download(ticker, period="6mo", session=yf_session)
                if isinstance(raw_df.columns, pd.MultiIndex):
                    raw_df.columns = raw_df.columns.get_level_values(0)
                if not raw_df.empty:
                    features_df = engineer_features_df(raw_df.copy())
            except Exception as yf_err:
                print(f"yfinance fetch failed for {ticker}: {yf_err}")

            if features_df is None or features_df.empty:
                features_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', safe_ticker, 'features.csv'))
                print(f"Falling back to cached CSV for {ticker}")
                features_df = pd.read_csv(features_path, index_col='Date', parse_dates=True)
                features_df.ffill(inplace=True)
                features_df.fillna(0, inplace=True)
            today_close = float(features_df['Close'].iloc[-1])
            current_prices[ticker] = today_close
            
            # Add to total portfolio value if we hold it
            if ticker in holdings:
                total_portfolio_value += holdings[ticker] * today_close
            
            # Update yesterday's prediction
            update_actual_price(ticker, today_close)
            
            # HMM Regime
            scaler_hmm = joblib.load(os.path.join(models_dir, "robust_scaler.pkl"))
            pca_hmm = joblib.load(os.path.join(models_dir, "pca_robust.pkl"))
            hmm_model_obj = joblib.load(os.path.join(models_dir, "hmm_model.pkl"))
            
            X_hmm = features_df[['Log_Return', 'Volatility_21d', 'Momentum_21d', 'MA_Dist_50d', 'Drawdown_252d', 'Volume_Ratio_21d']].copy()
            X_scaled_hmm = scaler_hmm.transform(X_hmm)
            X_pca_hmm = pca_hmm.transform(X_scaled_hmm)
            
            raw_regimes = hmm_model_obj.predict(X_pca_hmm)
            current_regime = hmm_model_obj.label_map_[raw_regimes[-1]]
            current_regimes[ticker] = current_regime
            
            # Predict Tomorrow (LSTM)
            scaler_X = joblib.load(os.path.join(models_dir, "lstm_scaler_X.pkl"))
            scaler_y = joblib.load(os.path.join(models_dir, "lstm_scaler_y.pkl"))
            input_size = scaler_X.n_features_in_
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            lstm_model = LSTMForecast(input_size=input_size).to(device)
            lstm_model.load_state_dict(torch.load(os.path.join(models_dir, "lstm_model.pth"), map_location=device))
            lstm_model.eval()
            
            probabilities = hmm_model_obj.predict_proba(X_pca_hmm)
            features_df['Prob_Bull'] = probabilities[:, 0]
            features_df['Prob_Sideways'] = probabilities[:, 1]
            features_df['Prob_Bear'] = probabilities[:, 2]
            
            lstm_feature_cols = ['Log_Return', 'Volatility_21d', 'Momentum_21d', 'MA_Dist_50d', 'Prob_Bull', 'Prob_Sideways', 'Prob_Bear']
            recent_data = features_df[lstm_feature_cols].tail(21).values
            recent_data_scaled = scaler_X.transform(recent_data)
            seq_tensor = torch.tensor(recent_data_scaled, dtype=torch.float32).unsqueeze(0).to(device)
            
            with torch.no_grad():
                pred_scaled = lstm_model(seq_tensor)
                
            predicted_log_return = scaler_y.inverse_transform(pred_scaled.cpu().numpy())[0][0]
            predicted_close = today_close * np.exp(predicted_log_return)
            log_prediction(ticker, predicted_close)
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
            
    # --- 2. SELL FIRST (Risk Management) ---
    for ticker, shares in list(holdings.items()):
        if shares > 0 and ticker in current_regimes:
            if current_regimes[ticker] == 2: # BEAR MARKET
                sell_value = shares * current_prices[ticker]
                cash += sell_value
                print(f"SELL: {ticker} hit BEAR regime. Sold {shares:.4f} shares for ${sell_value:.2f}")
                
                log_trade(ticker, "SELL", shares, current_prices[ticker], cash, total_portfolio_value)
                holdings[ticker] = 0.0

    # Clean up empty holdings
    holdings = {k: v for k, v in holdings.items() if v > 0}

    # --- 3. BUY SECOND (Capital Allocation) ---
    safe_tickers = [t for t, r in current_regimes.items() if r != 2] # Bull or Sideways
    
    # Calculate how much cash we want to allocate per safe ticker
    # We want an equal-weight portfolio of all safe assets.
    # Total portfolio value divided by number of safe assets = target allocation
    if len(safe_tickers) > 0:
        target_allocation_per_asset = total_portfolio_value / len(safe_tickers)
        
        for ticker in safe_tickers:
            current_investment = holdings.get(ticker, 0.0) * current_prices[ticker]
            # If we are under-allocated, buy more
            deficit = target_allocation_per_asset - current_investment
            
            # Only buy if the deficit is meaningful (e.g. > $10) and we have the cash
            if deficit > 10.0 and cash >= deficit:
                shares_to_buy = deficit / current_prices[ticker]
                cash -= deficit
                holdings[ticker] = holdings.get(ticker, 0.0) + shares_to_buy
                
                print(f"BUY: Allocated ${deficit:.2f} to {ticker} ({shares_to_buy:.4f} shares)")
                log_trade(ticker, "BUY", shares_to_buy, current_prices[ticker], cash, total_portfolio_value)

    update_portfolio(cash, holdings)
    
    print(f"Cycle Complete. Cash: ${cash:.2f} | Total Value: ${total_portfolio_value:.2f}")
    return {"status": "success", "cash": cash, "total_value": total_portfolio_value, "holdings": holdings}

if __name__ == "__main__":
    run_multi_asset_cycle()
