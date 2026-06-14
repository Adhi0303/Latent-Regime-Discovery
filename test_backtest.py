import pandas as pd
import numpy as np
import joblib

def test_backtest(ticker="^GSPC"):
    # Load models
    scaler = joblib.load(f"models/{ticker}/robust_scaler.pkl")
    pca = joblib.load(f"models/{ticker}/pca_robust.pkl")
    hmm = joblib.load(f"models/{ticker}/hmm_model.pkl")
    
    # Load data
    df = pd.read_csv(f"data/{ticker}/features.csv", index_col='Date', parse_dates=True)
    
    # Run HMM
    feature_cols = ['Log_Return', 'Volatility_21d', 'Momentum_21d', 'MA_Dist_50d', 'Drawdown_252d', 'Volume_Ratio_21d']
    X = df[feature_cols].copy()
    X_scaled = scaler.transform(X)
    X_pca = pca.transform(X_scaled)
    
    raw_regime_seq = hmm.predict(X_pca)
    label_map = hmm.label_map_
    regime_seq = np.array([label_map[l] for l in raw_regime_seq])
    
    df['Regime'] = regime_seq
    
    buy_hold = 10000.0
    ai_strategy = 10000.0
    
    history = []
    
    for i in range(1, len(df)):
        date = df.index[i].strftime('%Y-%m-%d')
        daily_return = float(df['Return'].iloc[i])
        
        # We trade based on yesterday's regime
        prev_regime = df['Regime'].iloc[i-1]
        
        buy_hold *= (1 + daily_return)
        
        # Regime 2 is typically Bear (based on volatility map, 2 is highest volatility)
        if prev_regime == 2:
            pass # Move to cash (no return)
        else:
            ai_strategy *= (1 + daily_return)
            
        history.append({
            "date": date,
            "buy_hold": buy_hold,
            "ai_strategy": ai_strategy
        })
        
    print(f"Buy & Hold Final: ${buy_hold:.2f}")
    print(f"AI Strategy Final: ${ai_strategy:.2f}")
    return history

if __name__ == "__main__":
    test_backtest()
