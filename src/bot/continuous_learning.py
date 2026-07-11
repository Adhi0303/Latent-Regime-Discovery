import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
import joblib
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.features.engineering import engineer_features_df
from src.models.train_lstm import LSTMForecast

TICKERS = ["^GSPC", "NVDA", "TSLA", "BTC-USD", "BRK-B"]

def create_sequences(data, target, seq_length):
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        x = data[i:(i + seq_length)]
        y = target[i + seq_length]
        xs.append(x)
        ys.append(y)
    return np.array(xs), np.array(ys)

def run_eod_retraining():
    print(f"\n--- Running End-Of-Day Continuous Learning Loop ({datetime.now()}) ---")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    for ticker in TICKERS:
        safe_ticker = ticker.replace("-", "_")
        models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', safe_ticker))
        
        if not os.path.exists(models_dir):
            continue
            
        print(f"\nRetraining {ticker}...")
        try:
            # 1. Fetch recent data (e.g., last 1 year of daily data)
            import time
            import random
            retries = 3
            raw_df = pd.DataFrame()
            
            for attempt in range(retries):
                try:
                    raw_df = yf.download(ticker, period="1y", interval="1d", progress=False)
                    if isinstance(raw_df.columns, pd.MultiIndex):
                        raw_df.columns = raw_df.columns.get_level_values(0)
                    if not raw_df.empty:
                        break
                except Exception as yf_err:
                    print(f"yfinance fetch failed for {ticker} (Attempt {attempt+1}/{retries}): {yf_err}")
                    if attempt < retries - 1:
                        time.sleep(random.uniform(2, 5) * (2 ** attempt))
            
            if raw_df.empty:
                print(f"Skipping {ticker} - no recent data fetched after {retries} attempts.")
                continue
                
            features_df = engineer_features_df(raw_df.copy())
            
            # 2. Get HMM Probabilities
            scaler_hmm = joblib.load(os.path.join(models_dir, "robust_scaler.pkl"))
            pca_hmm = joblib.load(os.path.join(models_dir, "pca_robust.pkl"))
            hmm_model_obj = joblib.load(os.path.join(models_dir, "hmm_model.pkl"))
            
            X_hmm = features_df[['Log_Return', 'Volatility_21d', 'Momentum_21d', 'MA_Dist_50d', 'Drawdown_252d', 'Volume_Ratio_21d']].copy()
            X_scaled_hmm = scaler_hmm.transform(X_hmm)
            X_pca_hmm = pca_hmm.transform(X_scaled_hmm)
            
            probabilities = hmm_model_obj.predict_proba(X_pca_hmm)
            features_df['Prob_Bull'] = probabilities[:, 0]
            features_df['Prob_Sideways'] = probabilities[:, 1]
            features_df['Prob_Bear'] = probabilities[:, 2]
            
            # 3. Prepare LSTM inputs
            scaler_X = joblib.load(os.path.join(models_dir, "lstm_scaler_X.pkl"))
            scaler_y = joblib.load(os.path.join(models_dir, "lstm_scaler_y.pkl"))
            
            lstm_feature_cols = ['Log_Return', 'Volatility_21d', 'Momentum_21d', 'MA_Dist_50d', 'Prob_Bull', 'Prob_Sideways', 'Prob_Bear']
            
            X_data = features_df[lstm_feature_cols].values
            y_data = features_df['Log_Return'].values.reshape(-1, 1) # Target is the next period's log return
            
            X_scaled = scaler_X.transform(X_data)
            y_scaled = scaler_y.transform(y_data)
            
            # Create sequences
            seq_length = 21
            X_seq, y_seq = create_sequences(X_scaled, y_scaled, seq_length)
            
            # We only want to train on the MOST RECENT sequences (e.g. this week/month)
            # A typical trading month has ~20 trading days. Let's train on the last 20 daily sequences.
            train_X = torch.tensor(X_seq[-20:], dtype=torch.float32).to(device)
            train_y = torch.tensor(y_seq[-20:], dtype=torch.float32).to(device)
            
            if len(train_X) == 0:
                print(f"Not enough data to retrain {ticker}.")
                continue
            
            # 4. Load Model
            input_size = scaler_X.n_features_in_
            lstm_model = LSTMForecast(input_size=input_size).to(device)
            model_path = os.path.join(models_dir, "lstm_model.pth")
            lstm_model.load_state_dict(torch.load(model_path, map_location=device))
            
            # 5. Continuous Learning (Fine-tuning)
            lstm_model.train()
            criterion = nn.MSELoss()
            optimizer = optim.Adam(lstm_model.parameters(), lr=0.0001) # Lower learning rate for fine-tuning
            
            epochs = 5 # Small number of epochs to prevent catastrophic forgetting
            for epoch in range(epochs):
                optimizer.zero_grad()
                outputs = lstm_model(train_X)
                loss = criterion(outputs, train_y)
                loss.backward()
                optimizer.step()
                
            print(f"Successfully retrained {ticker}. Final Loss: {loss.item():.6f}")
            
            # 6. Save updated model
            torch.save(lstm_model.state_dict(), model_path)
            
        except Exception as e:
            print(f"Error retraining {ticker}: {e}")

if __name__ == "__main__":
    run_eod_retraining()
