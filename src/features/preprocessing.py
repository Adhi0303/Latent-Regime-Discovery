import pandas as pd
import numpy as np
import os
import joblib
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA

def load_and_clean_features(input_path="data/features_sp500.csv"):
    """
    Loads engineered features and drops redundant/non-modeling columns.
    """
    print(f"Loading features from {input_path}...")
    df = pd.read_csv(input_path, index_col='Date', parse_dates=True)
    
    # Drop 'Close' because it's non-stationary (price level)
    # Drop 'Return' because it's perfectly correlated with 'Log_Return'
    cols_to_drop = []
    if 'Close' in df.columns:
        cols_to_drop.append('Close')
    if 'Return' in df.columns:
        cols_to_drop.append('Return')
        
    df_modeling = df.drop(columns=cols_to_drop)
    print(f"Dropped columns: {cols_to_drop}")
    print(f"Features kept for modeling: {list(df_modeling.columns)}")
    
    return df, df_modeling

def scale_features(df_modeling):
    """
    Applies both StandardScaler and RobustScaler to the features.
    Returns the scaled DataFrames and the fitted scaler objects.
    """
    print("Applying StandardScaler and RobustScaler...")
    
    # Standard Scaler (mean=0, variance=1)
    std_scaler = StandardScaler()
    std_scaled_data = std_scaler.fit_transform(df_modeling)
    df_std = pd.DataFrame(std_scaled_data, columns=df_modeling.columns, index=df_modeling.index)
    
    # Robust Scaler (uses median and IQR, robust to outliers)
    robust_scaler = RobustScaler()
    robust_scaled_data = robust_scaler.fit_transform(df_modeling)
    df_robust = pd.DataFrame(robust_scaled_data, columns=df_modeling.columns, index=df_modeling.index)
    
    return df_std, df_robust, std_scaler, robust_scaler

def apply_pca(df_scaled, n_components=0.95):
    """
    Applies PCA to the scaled features.
    n_components=0.95 means keep enough components to explain 95% of the variance.
    Alternatively, can pass an integer like 2 or 3.
    """
    print(f"Applying PCA (n_components={n_components})...")
    pca = PCA(n_components=n_components)
    pca_data = pca.fit_transform(df_scaled)
    
    # Create DataFrame with PC columns
    pc_cols = [f'PC{i+1}' for i in range(pca_data.shape[1])]
    df_pca = pd.DataFrame(pca_data, columns=pc_cols, index=df_scaled.index)
    
    print(f"PCA preserved {pca.n_components_} components.")
    print(f"Explained variance ratio: {pca.explained_variance_ratio_}")
    print(f"Total explained variance: {np.sum(pca.explained_variance_ratio_):.4f}")
    
    return df_pca, pca

def run_preprocessing_pipeline(ticker="^GSPC", input_path=None, output_dir=None):
    """
    End-to-end preprocessing pipeline.
    """
    if input_path is None:
        safe_ticker = ticker.replace("-", "_")
        input_path = f"data/{safe_ticker}/features.csv"
    if output_dir is None:
        safe_ticker = ticker.replace("-", "_")
        output_dir = f"data/{safe_ticker}"

    df_original, df_modeling = load_and_clean_features(input_path)
    
    # 1. Scale
    df_std, df_robust, std_scaler, robust_scaler = scale_features(df_modeling)
    
    # Save scalers for production use later
    safe_ticker = ticker.replace("-", "_")
    models_dir = f'models/{safe_ticker}'
    os.makedirs(models_dir, exist_ok=True)
    joblib.dump(std_scaler, os.path.join(models_dir, 'std_scaler.pkl'))
    joblib.dump(robust_scaler, os.path.join(models_dir, 'robust_scaler.pkl'))
    
    # 2. PCA (using robust scaled data since financial data has fat tails)
    print("\nUsing Robust Scaled data for final PCA transformation...")
    df_pca_robust, pca_robust = apply_pca(df_robust, n_components=3)  # Hardcode 3 for 3D visualization options
    joblib.dump(pca_robust, os.path.join(models_dir, 'pca_robust.pkl'))
    
    # 3. Save processed datasets
    os.makedirs(output_dir, exist_ok=True)
    
    std_path = os.path.join(output_dir, "features_scaled_std.csv")
    robust_path = os.path.join(output_dir, "features_scaled_robust.csv")
    pca_path = os.path.join(output_dir, "features_pca_robust.csv")
    
    df_std.to_csv(std_path)
    df_robust.to_csv(robust_path)
    df_pca_robust.to_csv(pca_path)
    
    print(f"\nSaved standardized features to {std_path}")
    print(f"Saved robust-scaled features to {robust_path}")
    print(f"Saved PCA features to {pca_path}")
    
    return df_modeling, df_std, df_robust, df_pca_robust, pca_robust

if __name__ == "__main__":
    run_preprocessing_pipeline()
