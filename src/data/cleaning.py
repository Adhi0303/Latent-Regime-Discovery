import pandas as pd
import os

def clean_market_data(ticker="^GSPC", input_path=None, output_path=None):
    """
    Cleans the raw market data by handling missing values, 
    zero-volume days, and ensuring a continuous timeline.
    """
    if input_path is None:
        safe_ticker = ticker.replace("-", "_")
        input_path = f"data/{safe_ticker}/raw.csv"
    if output_path is None:
        safe_ticker = ticker.replace("-", "_")
        output_path = f"data/{safe_ticker}/cleaned.csv"
        
    print(f"Loading raw data for {ticker} from {input_path}...")
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} does not exist. Please run ingestion.py first.")
        return None
        
    # Modern yfinance saves a multi-level header, we read it and drop the 'Ticker' level
    df = pd.read_csv(input_path, header=[0, 1], index_col=0, parse_dates=True)
    df.columns = df.columns.droplevel(1)
    df.index.name = 'Date'
    
    initial_rows = len(df)
    print(f"Initial shape: {df.shape}")
    
    # 1. Handle missing values (NaNs)
    # Forward-fill missing values (assume price stays the same as the previous day)
    missing_count = df.isnull().sum().sum()
    if missing_count > 0:
        print(f"Found {missing_count} missing values. Forward-filling...")
        df.ffill(inplace=True)
    
    # 2. Handle zero-volume days
    # Sometimes half-days or glitches result in 0 volume. 
    zero_volume_days = len(df[df['Volume'] == 0])
    if zero_volume_days > 0:
        print(f"Found {zero_volume_days} days with 0 volume. Replacing 0 with previous day's volume to avoid division-by-zero errors in feature engineering...")
        df['Volume'] = df['Volume'].replace(0, pd.NA)
        df['Volume'] = df['Volume'].ffill()
    
    # 3. Ensure strictly business days (Optional but good for completeness)
    # This creates a perfect Mon-Fri timeline, filling in missing holidays with the previous day's data.
    # We use 'B' for business day frequency
    all_weekdays = pd.date_range(start=df.index.min(), end=df.index.max(), freq='B')
    
    # Reindex the dataframe to include all weekdays
    # If a holiday was missing, it now appears as NaN
    df = df.reindex(all_weekdays)
    
    # Forward fill the newly created NaN rows (holidays)
    holidays_filled = df.isnull().sum().max()
    if holidays_filled > 0:
        print(f"Filled {holidays_filled} missing weekday records (likely bank holidays).")
        df.ffill(inplace=True)
        
    final_rows = len(df)
    print(f"Final shape: {df.shape} (Added {final_rows - initial_rows} rows for continuous timeline)")
    
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the cleaned data
    # Reset index to make 'Date' a normal column again for saving
    df.index.name = 'Date'
    df.to_csv(output_path)
    print(f"Cleaned data saved to {output_path}")
    
    return df

if __name__ == "__main__":
    clean_market_data()
