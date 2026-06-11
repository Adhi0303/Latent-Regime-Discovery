import yfinance as yf
import pandas as pd
import os
from datetime import datetime

def fetch_ticker_data(ticker="^GSPC", start_date="2005-01-01", end_date=None, output_path=None):
    """
    Fetches historical OHLCV data for a given ticker.
    
    Args:
        ticker (str): The ticker symbol.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format. Defaults to today.
        output_path (str): The path where the CSV will be saved.
    """
    if output_path is None:
        # Avoid invalid folder names for crypto
        safe_ticker = ticker.replace("-", "_")
        output_path = f"data/{safe_ticker}/raw.csv"
        
    print(f"Fetching {ticker} data from {start_date} to {end_date if end_date else 'today'}...")
    
    if not end_date:
        end_date = datetime.today().strftime('%Y-%m-%d')
        
    # Download the data
    df = yf.download(ticker, start=start_date, end=end_date)
    
    if df.empty:
        print(f"Error: No data fetched for {ticker}. Please check your internet connection or ticker symbol.")
        return None
        
    print(f"Successfully fetched {len(df)} rows of data for {ticker}.")
    
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path)
    print(f"Data saved to {output_path}")
    
    return df

if __name__ == "__main__":
    # Execute the function when the script is run directly
    fetch_ticker_data()
