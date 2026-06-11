import pandas as pd
import numpy as np
import os

def engineer_features_df(df):
    """
    Transforms raw OHLCV market data into stationary, relative features
    suitable for Hidden Markov Model regime discovery.
    Operates entirely in-memory on a Pandas DataFrame.
    """
    # 1. Simple Daily Returns
    df['Return'] = df['Close'].pct_change()
    
    # 2. Log Returns (Symmetric and additive)
    df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
    
    # 3. Rolling 21-Day Volatility (Realized Volatility)
    df['Volatility_21d'] = df['Log_Return'].rolling(window=21).std() * np.sqrt(252)

    # 4. 21-Day Momentum
    df['Momentum_21d'] = df['Close'].pct_change(periods=21)
    
    # 5. Moving Average Distance (Price vs 50-day MA)
    ma_50 = df['Close'].rolling(window=50).mean()
    df['MA_Dist_50d'] = (df['Close'] - ma_50) / ma_50
    
    # 6. Maximum Drawdown (252-Day Window)
    rolling_max_252 = df['Close'].rolling(window=252, min_periods=1).max()
    df['Drawdown_252d'] = (df['Close'] - rolling_max_252) / rolling_max_252
    
    # 7. Relative Volume Ratio
    ma_vol_21 = df['Volume'].rolling(window=21).mean()
    df['Volume_Ratio_21d'] = df['Volume'] / ma_vol_21
    
    # Cleanup NaN values
    df.dropna(inplace=True)
    
    feature_cols = [
        'Close',
        'Return', 
        'Log_Return', 
        'Volatility_21d', 
        'Momentum_21d', 
        'MA_Dist_50d', 
        'Drawdown_252d', 
        'Volume_Ratio_21d'
    ]
    
    return df[feature_cols]

def engineer_features(ticker="^GSPC", input_path=None, output_path=None):
    """
    Wrapper for offline CSV processing.
    """
    if input_path is None:
        safe_ticker = ticker.replace("-", "_")
        input_path = f"data/{safe_ticker}/cleaned.csv"
    if output_path is None:
        safe_ticker = ticker.replace("-", "_")
        output_path = f"data/{safe_ticker}/features.csv"

    print(f"Loading cleaned data for {ticker} from {input_path}...")
    if not os.path.exists(input_path):
        print(f"Error: {input_path} does not exist. Please run data/cleaning.py first.")
        return None
        
    df = pd.read_csv(input_path, index_col='Date', parse_dates=True)
    
    features_df = engineer_features_df(df)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    features_df.to_csv(output_path)
    print(f"Engineered features successfully saved to {output_path}")
    
    return features_df

if __name__ == "__main__":
    engineer_features()
