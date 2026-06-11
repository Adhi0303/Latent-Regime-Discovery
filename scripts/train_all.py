import os
import sys

# Add the project root to the python path so 'src' module can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.ingestion import fetch_ticker_data
from src.data.cleaning import clean_market_data
from src.features.engineering import engineer_features
from src.features.preprocessing import run_preprocessing_pipeline
from src.models.baseline_clustering import run_clustering_pipeline
from src.models.hmm_regimes import run_hmm_pipeline

TICKERS = ["^GSPC", "BTC-USD", "TSLA", "NVDA", "BRK-B"]

def main():
    print("========================================")
    print("   MULTI-ASSET REGIME MODEL TRAINING    ")
    print("========================================")
    
    for ticker in TICKERS:
        print(f"\n\n>>> PROCESSING TICKER: {ticker}")
        print("-" * 40)
        
        # 1. Ingestion
        df_raw = fetch_ticker_data(ticker=ticker)
        if df_raw is None:
            print(f"Skipping {ticker} due to data fetching error.")
            continue
            
        # 2. Cleaning
        df_clean = clean_market_data(ticker=ticker)
        
        # 3. Engineering
        df_feat = engineer_features(ticker=ticker)
        
        # 4. Preprocessing (Scaling & PCA)
        run_preprocessing_pipeline(ticker=ticker)
        
        # 5. Baseline Clustering (K-Means & GMM)
        run_clustering_pipeline(ticker=ticker)
        
        # 6. HMM Regime Modeling
        run_hmm_pipeline(ticker=ticker)
        
        print(f"\n<<< SUCCESSFULLY COMPLETED {ticker}")
        
    print("\n========================================")
    print("       ALL ASSETS PROCESSED             ")
    print("========================================")

if __name__ == "__main__":
    main()
