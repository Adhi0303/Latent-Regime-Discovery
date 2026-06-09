import pandas as pd
import numpy as np
import os

def engineer_features(input_path="data/cleaned_sp500.csv", output_path="data/features_sp500.csv"):
    """
    Transforms raw OHLCV market data into stationary, relative features
    suitable for Hidden Markov Model regime discovery.
    """
    print(f"Loading cleaned data from {input_path}...")
    if not os.path.exists(input_path):
        print(f"Error: {input_path} does not exist. Please run data/cleaning.py first.")
        return None
        
    df = pd.read_csv(input_path, index_col='Date', parse_dates=True)
    
    # ---------------------------------------------------------
    # Module 3.1: Price & Volatility Transformations
    # ---------------------------------------------------------
    print("Calculating Price & Volatility Transformations...")
    
    # 1. Simple Daily Returns
    df['Return'] = df['Close'].pct_change()
    
    # 2. Log Returns (Symmetric and additive)
    df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
    
    # 3. Rolling 21-Day Volatility (Realized Volatility)
    # Multiplying by sqrt(252) annualizes the volatility, which is standard in finance
    df['Volatility_21d'] = df['Log_Return'].rolling(window=21).std() * np.sqrt(252)

    # ---------------------------------------------------------
    # Module 3.2: Trend, Momentum & Stress Indicators
    # ---------------------------------------------------------
    print("Calculating Trend, Momentum & Stress Indicators...")
    
    # 1. 21-Day Momentum
    df['Momentum_21d'] = df['Close'].pct_change(periods=21)
    
    # 2. Moving Average Distance (Price vs 50-day MA)
    ma_50 = df['Close'].rolling(window=50).mean()
    df['MA_Dist_50d'] = (df['Close'] - ma_50) / ma_50
    
    # 3. Maximum Drawdown (252-Day Window)
    # Drawdown is how far we've fallen from the highest point in the last year
    rolling_max_252 = df['Close'].rolling(window=252, min_periods=1).max()
    df['Drawdown_252d'] = (df['Close'] - rolling_max_252) / rolling_max_252
    
    # 4. Relative Volume Ratio
    # Compare today's volume to the average volume over the last 21 days
    ma_vol_21 = df['Volume'].rolling(window=21).mean()
    df['Volume_Ratio_21d'] = df['Volume'] / ma_vol_21
    
    # ---------------------------------------------------------
    # Cleanup & Formatting
    # ---------------------------------------------------------
    print("Cleaning up NaN values caused by rolling windows...")
    
    # Because we used a 50-day moving average, the first 50 rows will have NaNs.
    # The max drawdown uses 252 days, but we used min_periods=1 so it won't drop everything, 
    # but the 50d MA and 21d rolling will definitely create NaNs.
    # We drop any row that has a NaN to ensure the ML model gets perfect data.
    
    initial_len = len(df)
    df.dropna(inplace=True)
    final_len = len(df)
    
    print(f"Dropped {initial_len - final_len} rows due to lookback periods.")
    print(f"Final feature dataset shape: {df.shape}")
    
    # Keep only the engineered features for the ML models, optionally keep 'Close' for charting later
    feature_cols = [
        'Close', # Keeping this strictly for later dashboard plotting
        'Return', 
        'Log_Return', 
        'Volatility_21d', 
        'Momentum_21d', 
        'MA_Dist_50d', 
        'Drawdown_252d', 
        'Volume_Ratio_21d'
    ]
    
    features_df = df[feature_cols]
    
    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    features_df.to_csv(output_path)
    print(f"Engineered features successfully saved to {output_path}")
    
    return features_df

if __name__ == "__main__":
    engineer_features()
