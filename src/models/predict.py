import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
import joblib
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.features.engineering import engineer_features_df

# Human-readable labels for regimes
REGIME_LABELS = {
    0: "Bull Market (Low Volatility)",
    1: "Sideways / Correction (Medium Volatility)",
    2: "Bear Market / Crisis (High Volatility)"
}

def get_live_data(ticker="^GSPC", period="2y"):
    """
    Downloads live market data from Yahoo Finance.
    We need at least 252 days for the Max Drawdown calculation.
    """
    print(f"Fetching live data for {ticker} over the last {period}...")
    df = yf.download(ticker, period=period)
    
    # yfinance sometimes returns multi-index columns, flatten if needed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    return df

def load_pipeline_models(models_dir="models"):
    """
    Loads the trained scaler, PCA, and HMM models.
    """
    try:
        scaler = joblib.load(os.path.join(models_dir, "robust_scaler.pkl"))
        pca = joblib.load(os.path.join(models_dir, "pca_robust.pkl"))
        hmm_model = joblib.load(os.path.join(models_dir, "hmm_model.pkl"))
        return scaler, pca, hmm_model
    except FileNotFoundError as e:
        print(f"Error loading models: {e}")
        print("Please ensure you have run the full training pipeline first.")
        sys.exit(1)

def predict_live_regime():
    """
    End-to-end pipeline to predict today's market regime.
    """
    print(f"--- Latent Regime Discovery: Live Prediction Pipeline ---\n")
    print(f"Current Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Fetch live data
    raw_df = get_live_data()
    
    # 2. Engineer features
    print("Engineering features in-memory...")
    features_df = engineer_features_df(raw_df)
    
    # Keep only the numerical features used for scaling (drop Close and Return)
    feature_cols = [
        'Log_Return', 'Volatility_21d', 'Momentum_21d', 
        'MA_Dist_50d', 'Drawdown_252d', 'Volume_Ratio_21d'
    ]
    
    X = features_df[feature_cols]
    latest_date = X.index[-1].strftime('%Y-%m-%d')
    latest_close = features_df['Close'].iloc[-1]
    
    # 3. Load Models
    print("Loading AI pipeline models (Scaler -> PCA -> HMM)...")
    scaler, pca, hmm_model = load_pipeline_models()
    
    # 4. Transform data
    # We must transform the entire series or just the latest row. 
    # Usually we transform the entire series to be safe and use the last row.
    X_scaled = scaler.transform(X)
    X_pca = pca.transform(X_scaled)
    
    # 5. Predict Regime for today
    print("Calculating live transition probabilities...")
    # Get the last row for today's data
    today_pca = X_pca[-1].reshape(1, -1)
    
    # We predict the sequence up to today to let the HMM use its Markov property
    # Viterbi algorithm runs on the sequence
    regime_sequence = hmm_model.predict(X_pca)
    probabilities = hmm_model.predict_proba(X_pca)
    
    today_regime = regime_sequence[-1]
    today_probs = probabilities[-1]
    
    print("\n" + "="*50)
    print(f"LATEST MARKET DATA ({latest_date})")
    print(f"S&P 500 Close Price: ${latest_close:,.2f}")
    print("="*50)
    
    print(f"\n[ LIVE AI PREDICTION ]")
    print(f"Current Market Regime: >> {REGIME_LABELS[today_regime].upper()} <<\n")
    
    print("Regime Probability Breakdown:")
    for regime_id, label in REGIME_LABELS.items():
        prob = today_probs[regime_id] * 100
        print(f" - {label:<45}: {prob:6.2f}%")
        
    print("\nPipeline execution complete.")

if __name__ == "__main__":
    predict_live_regime()
