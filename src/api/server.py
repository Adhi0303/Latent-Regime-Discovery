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
import asyncio
import schedule
import requests
from contextlib import asynccontextmanager

yf_session = requests.Session()
yf_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
})

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.features.engineering import engineer_features_df
from src.data.news_scraper import fetch_recent_news
from src.models.sentiment_agent import get_sentiment_analyst

async def run_scheduler():
    """Background task to run the scheduler."""
    from src.bot.scheduler import setup_scheduler
    setup_scheduler()
    while True:
        await asyncio.to_thread(schedule.run_pending)
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    load_models_on_startup()
    asyncio.create_task(run_scheduler())
    yield
    # Shutdown logic could go here

app = FastAPI(title="Latent Regime Discovery API", lifespan=lifespan)

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

def load_models_on_startup():
    """Loads pre-trained models on startup for all supported tickers."""
    models_dir_base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models'))
    TICKERS = ["^GSPC", "BTC-USD", "TSLA", "NVDA", "BRK-B"]
    
    for ticker in TICKERS:
        safe_ticker = ticker.replace("-", "_")
        models_dir = os.path.join(models_dir_base, safe_ticker)
        try:
            models[ticker] = {
                'scaler': joblib.load(os.path.join(models_dir, "robust_scaler.pkl")),
                'pca': joblib.load(os.path.join(models_dir, "pca_robust.pkl")),
                'hmm': joblib.load(os.path.join(models_dir, "hmm_model.pkl"))
            }
            print(f"Models loaded successfully for {ticker}.")
        except Exception as e:
            print(f"Warning: Failed to load models for {ticker}. {e}")

    print("Loading FinBERT sentiment model...")
    try:
        get_sentiment_analyst()
        print("FinBERT loaded successfully.")
    except Exception as e:
        print(f"Warning: Failed to load FinBERT. {e}")

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
    if ticker not in models or "hmm" not in models[ticker]:
        raise HTTPException(status_code=500, detail=f"Models are not loaded for {ticker}.")
        
    scaler = models[ticker]['scaler']
    pca = models[ticker]['pca']
    hmm_model = models[ticker]['hmm']
    
    # 1. Fetch Data — try live first, fall back to cached CSV
    safe_ticker = ticker.replace("-", "_")
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', safe_ticker))
    features_path = os.path.join(data_dir, "features.csv")
    
    features_df = None
    try:
        raw_df = yf.download(ticker, period=period, session=yf_session, timeout=5)
        if isinstance(raw_df.columns, pd.MultiIndex):
            raw_df.columns = raw_df.columns.get_level_values(0)
        if not raw_df.empty:
            features_df = engineer_features_df(raw_df.copy())
    except Exception as e:
        print(f"yfinance failed for {ticker}: {e}. Falling back to cached CSV.")
    
    # Fall back to pre-cached CSV if live fetch failed
    if features_df is None or features_df.empty:
        if not os.path.exists(features_path):
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}.")
        features_df = pd.read_csv(features_path, index_col='Date', parse_dates=True)
        features_df.ffill(inplace=True)
        features_df.fillna(0, inplace=True)

    feature_cols = [
        'Log_Return', 'Volatility_21d', 'Momentum_21d', 
        'MA_Dist_50d', 'Drawdown_252d', 'Volume_Ratio_21d'
    ]
    X = features_df[feature_cols].copy()
    
    # 3. Transform & Predict
    X_scaled = scaler.transform(X)
    X_pca = pca.transform(X_scaled)
    
    raw_regime_seq = hmm_model.predict(X_pca)
    raw_probs = hmm_model.predict_proba(X_pca)
    
    # Apply the volatility sorting map saved during training
    label_map = hmm_model.label_map_
    regime_seq = np.array([label_map[l] for l in raw_regime_seq])
    
    # Sort probabilities to match the mapped regimes
    probs = np.zeros_like(raw_probs)
    for old_l, new_l in label_map.items():
        probs[:, new_l] = raw_probs[:, old_l]
        
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

@app.get("/api/backtest")
def get_backtest(ticker: str = "^GSPC"):
    """
    Simulates a $10,000 portfolio over the available history.
    Buy & Hold vs AI Strategy (moves to cash during Bear Regimes).
    """
    safe_ticker = ticker.replace("-", "_")
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', safe_ticker))
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', safe_ticker))
    
    try:
        scaler = joblib.load(os.path.join(models_dir, "robust_scaler.pkl"))
        pca = joblib.load(os.path.join(models_dir, "pca_robust.pkl"))
        hmm = joblib.load(os.path.join(models_dir, "hmm_model.pkl"))
        
        features_path = os.path.join(data_dir, "features.csv")
        if not os.path.exists(features_path):
            raise HTTPException(status_code=404, detail="Historical data not found. Run engineering.py")
            
        df = pd.read_csv(features_path, index_col='Date', parse_dates=True)
        
        feature_cols = ['Log_Return', 'Volatility_21d', 'Momentum_21d', 'MA_Dist_50d', 'Drawdown_252d', 'Volume_Ratio_21d']
        X = df[feature_cols].copy()
        
        # We need to fill NaNs if any exist to prevent HMM crash
        X.ffill(inplace=True)
        X.fillna(0, inplace=True)
        
        X_scaled = scaler.transform(X)
        X_pca = pca.transform(X_scaled)
        
        raw_regime_seq = hmm.predict(X_pca)
        label_map = hmm.label_map_
        regime_seq = np.array([label_map[l] for l in raw_regime_seq])
        
        df['Regime'] = regime_seq
        
        buy_hold_val = 10000.0
        ai_val = 10000.0
        
        bh_peak = buy_hold_val
        ai_peak = ai_val
        
        bh_max_dd = 0.0
        ai_max_dd = 0.0
        
        history = []
        
        for i in range(1, len(df)):
            date_str = df.index[i].strftime('%Y-%m-%d')
            daily_return = float(df['Return'].iloc[i])
            
            # Predict using T-1 regime to avoid lookahead bias
            prev_regime = df['Regime'].iloc[i-1]
            
            buy_hold_val *= (1 + daily_return)
            
            # Regime 2 is Bear Market (High Volatility, Negative Return)
            if prev_regime == 2:
                # Move to cash (0% return)
                pass
            else:
                ai_val *= (1 + daily_return)
                
            # Drawdown calcs
            if buy_hold_val > bh_peak: bh_peak = buy_hold_val
            if ai_val > ai_peak: ai_peak = ai_val
            
            bh_dd = (buy_hold_val - bh_peak) / bh_peak
            ai_dd = (ai_val - ai_peak) / ai_peak
            
            if bh_dd < bh_max_dd: bh_max_dd = bh_dd
            if ai_dd < ai_max_dd: ai_max_dd = ai_dd
            
            # Sub-sample data to prevent massive payloads (take every 5th day, or end of month)
            # Or just send everything and let recharts handle it. Let's sample 1 per week approx for speed
            if i % 5 == 0 or i == len(df) - 1:
                history.append({
                    "date": date_str,
                    "buy_hold": round(buy_hold_val, 2),
                    "ai_strategy": round(ai_val, 2)
                })
                
        bh_total_ret = ((buy_hold_val - 10000) / 10000) * 100
        ai_total_ret = ((ai_val - 10000) / 10000) * 100
        alpha = ai_total_ret - bh_total_ret
        
        return {
            "ticker": ticker,
            "metrics": {
                "buy_hold_return": round(bh_total_ret, 2),
                "ai_return": round(ai_total_ret, 2),
                "alpha": round(alpha, 2),
                "buy_hold_max_dd": round(bh_max_dd * 100, 2),
                "ai_max_dd": round(ai_max_dd * 100, 2)
            },
            "history": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {e}")

@app.get("/api/bot/portfolio")
def get_bot_portfolio():
    """Returns the live unified portfolio status, holdings, and global ledger."""
    import sqlite3
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'trading_bot.db'))
    if not os.path.exists(db_path):
        return {"cash_balance": 10000.0, "holdings": {}, "ledger": []}
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Portfolio Status
    cursor.execute('SELECT cash_balance FROM portfolio_status WHERE id = 1')
    row = cursor.fetchone()
    cash_balance = row[0] if row else 10000.0
    
    # Holdings and their latest price
    cursor.execute('SELECT ticker, amount FROM holdings')
    holdings_rows = cursor.fetchall()
    
    holdings = []
    for r in holdings_rows:
        ticker = r[0]
        amount = r[1]
        
        # Get the latest price for this ticker from the ledger
        cursor.execute('''
            SELECT price FROM ledger 
            WHERE ticker = ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (ticker,))
        price_row = cursor.fetchone()
        latest_price = price_row[0] if price_row else 0.0
        
        value = amount * latest_price
        
        holdings.append({
            "ticker": ticker, 
            "amount": amount,
            "latest_price": latest_price,
            "value": value
        })
    
    # Ledger
    cursor.execute('''
        SELECT timestamp, ticker, action, shares_traded, price, cash_after, portfolio_value_after 
        FROM ledger ORDER BY timestamp DESC LIMIT 100
    ''')
    ledger_rows = cursor.fetchall()
    ledger = []
    for r in ledger_rows:
        ledger.append({
            "timestamp": r[0],
            "ticker": r[1],
            "action": r[2],
            "shares_traded": r[3],
            "price": r[4],
            "cash_after": r[5],
            "portfolio_value_after": r[6]
        })
        
    conn.close()
    return {"cash_balance": cash_balance, "holdings": holdings, "ledger": ledger}

@app.get("/api/bot/predictions")
def get_bot_predictions(ticker: str = "^GSPC"):
    """Returns the historical Predicted vs Actual prices and MAE."""
    import sqlite3
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'trading_bot.db'))
    if not os.path.exists(db_path):
        return {"predictions": [], "mae": 0.0}
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, predicted_close, actual_close, error_pct 
        FROM predictions WHERE ticker = ? ORDER BY timestamp ASC
    ''', (ticker,))
    rows = cursor.fetchall()
    conn.close()
    
    predictions = []
    total_error = 0
    count = 0
    
    for r in rows:
        predictions.append({
            "timestamp": r[0],
            "predicted_close": r[1],
            "actual_close": r[2]
        })
        if r[3] is not None:
            total_error += r[3]
            count += 1
            
    mae = (total_error / count) if count > 0 else 0.0
    
    return {"predictions": predictions, "mae": mae}

@app.post("/api/bot/run")
def force_bot_run():
    """WebHook to manually trigger the multi-asset paper trading bot's daily cycle."""
    from src.bot.paper_trader import run_multi_asset_cycle
    try:
        res = run_multi_asset_cycle()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot cycle failed: {e}")

@app.post("/api/bot/retrain")
def force_retrain_check():
    """WebHook to manually trigger the Auto-Retrainer Heartbeat Monitor (Macro)."""
    from src.bot.retrainer import check_and_retrain
    try:
        res = check_and_retrain()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrainer check failed: {e}")

@app.post("/api/bot/continuous_learn")
def force_continuous_learn():
    """WebHook to manually trigger the Intraday End-Of-Day Continuous Learning fine-tuning."""
    from src.bot.continuous_learning import run_eod_retraining
    try:
        run_eod_retraining()
        return {"status": "success", "message": "Continuous learning epoch completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Continuous learning failed: {e}")

@app.get("/api/sentiment")
def get_sentiment(ticker: str = "^GSPC"):
    """
    Fetches the latest news for the ticker and scores it using FinBERT.
    """
    try:
        news = fetch_recent_news(ticker, limit=5)
        analyst = get_sentiment_analyst()
        macro_score, scored_news = analyst.analyze_headlines(news)
        
        return {
            "ticker": ticker,
            "macro_score": macro_score,
            "news": scored_news
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {e}")

@app.get("/api/forecast")
def get_forecast(ticker: str = "^GSPC"):
    """
    Predicts tomorrow's closing price using the PyTorch LSTM model.
    Then, it uses an Ensemble approach to adjust the prediction based on today's FinBERT Sentiment.
    """
    import torch
    from src.models.train_lstm import LSTMForecast
    
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', ticker.replace('-', '_')))
    
    try:
        # Load scalers and model
        scaler_X = joblib.load(os.path.join(models_dir, "lstm_scaler_X.pkl"))
        scaler_y = joblib.load(os.path.join(models_dir, "lstm_scaler_y.pkl"))
        
        # Determine input size from scaler
        input_size = scaler_X.n_features_in_
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        lstm_model = LSTMForecast(input_size=input_size).to(device)
        lstm_model.load_state_dict(torch.load(os.path.join(models_dir, "lstm_model.pth"), map_location=device))
        lstm_model.eval()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LSTM Models not found for {ticker}. Did you run train_lstm.py? {e}")

    try:
        # 1. Fetch Data — try live first, fall back to cached CSV
        safe_ticker_fcast = ticker.replace("-", "_")
        data_dir_fcast = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', safe_ticker_fcast))
        features_path_fcast = os.path.join(data_dir_fcast, "features.csv")
        
        features_df = None
        try:
            raw_df = yf.download(ticker, period="6mo", session=yf_session, timeout=5)
            if isinstance(raw_df.columns, pd.MultiIndex):
                raw_df.columns = raw_df.columns.get_level_values(0)
            if not raw_df.empty:
                features_df = engineer_features_df(raw_df.copy())
        except Exception as e:
            print(f"yfinance failed for {ticker} in forecast: {e}. Falling back to cached CSV.")
        
        if features_df is None or features_df.empty:
            if not os.path.exists(features_path_fcast):
                raise HTTPException(status_code=404, detail=f"No cached data for {ticker}.")
            features_df = pd.read_csv(features_path_fcast, index_col='Date', parse_dates=True)
            features_df.ffill(inplace=True)
            features_df.fillna(0, inplace=True)
        
        # HMM Probabilities
        scaler_hmm = models[ticker]['scaler']
        pca_hmm = models[ticker]['pca']
        hmm_model_obj = models[ticker]['hmm']
        
        X_hmm = features_df[['Log_Return', 'Volatility_21d', 'Momentum_21d', 'MA_Dist_50d', 'Drawdown_252d', 'Volume_Ratio_21d']].copy()
        X_scaled_hmm = scaler_hmm.transform(X_hmm)
        X_pca_hmm = pca_hmm.transform(X_scaled_hmm)
        probabilities = hmm_model_obj.predict_proba(X_pca_hmm)
        
        features_df['Prob_Bull'] = probabilities[:, 0]
        features_df['Prob_Sideways'] = probabilities[:, 1]
        features_df['Prob_Bear'] = probabilities[:, 2]
        
        lstm_feature_cols = [
            'Log_Return', 'Volatility_21d', 'Momentum_21d', 'MA_Dist_50d',
            'Prob_Bull', 'Prob_Sideways', 'Prob_Bear'
        ]
        
        # Extract the last 21 days
        if len(features_df) < 21:
            raise HTTPException(status_code=500, detail="Not enough data to form a 21-day sequence.")
            
        recent_data = features_df[lstm_feature_cols].tail(21).values
        
        # Scale the sequence
        recent_data_scaled = scaler_X.transform(recent_data)
        
        # Convert to tensor and add batch dimension: shape (1, 21, 7)
        seq_tensor = torch.tensor(recent_data_scaled, dtype=torch.float32).unsqueeze(0).to(device)
        
        # 2. Base Prediction from LSTM
        with torch.no_grad():
            pred_scaled = lstm_model(seq_tensor)
            
        # Inverse transform to get predicted Log_Return
        predicted_log_return = scaler_y.inverse_transform(pred_scaled.cpu().numpy())[0][0]
        
        current_close = float(features_df['Close'].iloc[-1])
        
        # Convert Log_Return to expected Dollar Amount: Price_t+1 = Price_t * exp(Log_Return)
        base_prediction = current_close * np.exp(predicted_log_return)
        
        # 3. Ensemble Adjustment via RAG Sentiment
        # Get live sentiment score
        news = fetch_recent_news(ticker, limit=5)
        analyst = get_sentiment_analyst()
        macro_score, _ = analyst.analyze_headlines(news)
        
        # Calculate adjustment
        # e.g., A +1.0 sentiment could boost the price prediction by +0.5% (a realistic single-day drift)
        # A -1.0 sentiment drops it by -0.5%
        adjustment_multiplier = 1.0 + (macro_score * 0.005) 
        
        final_prediction = base_prediction * adjustment_multiplier
        
        pct_change = ((final_prediction - current_close) / current_close) * 100
        
        return {
            "ticker": ticker,
            "current_price": current_close,
            "base_lstm_prediction": float(base_prediction),
            "sentiment_score": macro_score,
            "final_prediction": float(final_prediction),
            "predicted_pct_change": float(pct_change)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting pipeline failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True)
