import os
import sys
import pandas as pd
import numpy as np
import torch
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.models.predict import load_pipeline_models

def prepare_lstm_data(ticker="^GSPC", sequence_length=21, test_size=0.1):
    """
    Prepares the historical data for the LSTM.
    It combines market features with the HMM regime probabilities,
    scales them, and generates sliding-window sequences.
    """
    safe_ticker = ticker.replace("-", "_")
    features_path = f"data/{safe_ticker}/features.csv"
    models_dir = f"models/{safe_ticker}"
    
    if not os.path.exists(features_path):
        print(f"Error: {features_path} not found. Please run engineering.py first.")
        return None
        
    df = pd.read_csv(features_path, index_col='Date', parse_dates=True)
    
    # 1. Generate Historical HMM Probabilities
    # We need to run the HMM on the historical data to get the regime probabilities
    feature_cols = [
        'Log_Return', 'Volatility_21d', 'Momentum_21d', 
        'MA_Dist_50d', 'Drawdown_252d', 'Volume_Ratio_21d'
    ]
    X_hmm_input = df[feature_cols]
    
    scaler_hmm, pca_hmm, hmm_model = load_pipeline_models(models_dir)
    
    X_scaled_hmm = scaler_hmm.transform(X_hmm_input)
    X_pca_hmm = pca_hmm.transform(X_scaled_hmm)
    
    probabilities = hmm_model.predict_proba(X_pca_hmm)
    
    df['Prob_Bull'] = probabilities[:, 0]
    df['Prob_Sideways'] = probabilities[:, 1]
    df['Prob_Bear'] = probabilities[:, 2]
    
    # 2. Define our final LSTM Features
    lstm_feature_cols = [
        'Log_Return', 'Volatility_21d', 'Momentum_21d', 'MA_Dist_50d',
        'Prob_Bull', 'Prob_Sideways', 'Prob_Bear'
    ]
    
    # Target is predicting the NEXT day's return
    df['Target_Return'] = df['Log_Return'].shift(-1)
    
    # Drop the last row since it doesn't have a next day target
    df.dropna(inplace=True)
    
    X_data = df[lstm_feature_cols].values
    y_data = df[['Target_Return']].values
    
    # 3. Scale the Data (Neural Networks need inputs between 0 and 1)
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    
    X_scaled = scaler_X.fit_transform(X_data)
    y_scaled = scaler_y.fit_transform(y_data)
    
    # Save scalers for live forecasting later
    os.makedirs(models_dir, exist_ok=True)
    joblib.dump(scaler_X, os.path.join(models_dir, "lstm_scaler_X.pkl"))
    joblib.dump(scaler_y, os.path.join(models_dir, "lstm_scaler_y.pkl"))
    
    # 4. Generate Sliding Window Sequences
    X_seq, y_seq = [], []
    for i in range(len(X_scaled) - sequence_length):
        X_seq.append(X_scaled[i:(i + sequence_length)])
        y_seq.append(y_scaled[i + sequence_length])
        
    X_seq = np.array(X_seq)
    y_seq = np.array(y_seq)
    
    # 5. Train / Test Split
    split_idx = int(len(X_seq) * (1 - test_size))
    
    X_train, X_test = X_seq[:split_idx], X_seq[split_idx:]
    y_train, y_test = y_seq[:split_idx], y_seq[split_idx:]
    
    # Convert to PyTorch Tensors
    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.float32)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)
    y_test_t = torch.tensor(y_test, dtype=torch.float32)
    
    print(f"[{ticker}] LSTM Data Prep Complete.")
    print(f"Sequence Length: {sequence_length}")
    print(f"Training Samples: {len(X_train_t)}, Testing Samples: {len(X_test_t)}")
    
    return X_train_t, y_train_t, X_test_t, y_test_t

if __name__ == "__main__":
    prepare_lstm_data("TSLA")
