import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.features.engineering import engineer_features_df

app = FastAPI(title="Latent Regime Discovery API")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development (e.g. localhost:3000)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model variables
models = {}

@app.on_event("startup")
def load_models_on_startup():
    """Loads pre-trained models on startup."""
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models'))
    try:
        models['scaler'] = joblib.load(os.path.join(models_dir, "robust_scaler.pkl"))
        models['pca'] = joblib.load(os.path.join(models_dir, "pca_robust.pkl"))
        models['hmm'] = joblib.load(os.path.join(models_dir, "hmm_model.pkl"))
        print("Models loaded successfully.")
    except Exception as e:
        print(f"Warning: Failed to load models. {e}")

class PredictRequest(BaseModel):
    ticker: str = "^GSPC"
    period: str = "5y"

@app.get("/api/health")
def health_check():
    return {"status": "ok", "models_loaded": "hmm" in models}

@app.get("/api/predict")
def predict_regime(ticker: str = "^GSPC", period: str = "5y"):
    """
    Fetches market data, runs the HMM pipeline, and returns the regimes.
    """
    if "hmm" not in models:
        raise HTTPException(status_code=500, detail="Models are not loaded.")
        
    scaler = models['scaler']
    pca = models['pca']
    hmm_model = models['hmm']
    
    # 1. Fetch Data
    try:
        raw_df = yf.download(ticker, period=period)
        if isinstance(raw_df.columns, pd.MultiIndex):
            raw_df.columns = raw_df.columns.get_level_values(0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch data: {e}")
        
    if raw_df.empty:
        raise HTTPException(status_code=404, detail="No data found for ticker.")

    # 2. Engineer Features
    try:
        features_df = engineer_features_df(raw_df.copy())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature engineering failed: {e}")

    feature_cols = [
        'Log_Return', 'Volatility_21d', 'Momentum_21d', 
        'MA_Dist_50d', 'Drawdown_252d', 'Volume_Ratio_21d'
    ]
    X = features_df[feature_cols].copy()
    
    # 3. Transform & Predict
    X_scaled = scaler.transform(X)
    X_pca = pca.transform(X_scaled)
    
    regime_seq = hmm_model.predict(X_pca)
    probs = hmm_model.predict_proba(X_pca)
    
    features_df['Regime'] = regime_seq
    
    # Prepare historical data for the chart
    # We will return the last 1000 days to avoid massive payloads, but 5y is ~1250 days.
    # Convert index to string dates
    features_df['Date'] = features_df.index.strftime('%Y-%m-%d')
    
    history = []
    for idx, row in features_df.iterrows():
        history.append({
            "date": row['Date'],
            "close": float(row['Close']),
            "regime": int(row['Regime'])
        })
        
    today_probs = probs[-1].tolist()
    
    response = {
        "ticker": ticker,
        "latest_date": features_df['Date'].iloc[-1],
        "latest_close": float(features_df['Close'].iloc[-1]),
        "current_regime": int(features_df['Regime'].iloc[-1]),
        "probabilities": {
            "0": today_probs[0],
            "1": today_probs[1],
            "2": today_probs[2]
        },
        "history": history
    }
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True)
