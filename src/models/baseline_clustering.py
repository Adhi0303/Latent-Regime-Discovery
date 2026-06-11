import pandas as pd
import numpy as np
import os
import joblib
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture

def load_data(pca_path="data/features_pca_robust.csv", orig_path="data/features_sp500.csv"):
    """
    Loads PCA components and original feature data.
    """
    print(f"Loading PCA features from {pca_path}...")
    df_pca = pd.read_csv(pca_path, index_col='Date', parse_dates=True)
    
    print(f"Loading original features from {orig_path}...")
    df_orig = pd.read_csv(orig_path, index_col='Date', parse_dates=True)
    
    # Ensure indices match
    common_idx = df_pca.index.intersection(df_orig.index)
    df_pca = df_pca.loc[common_idx]
    df_orig = df_orig.loc[common_idx]
    
    return df_pca, df_orig

def train_kmeans(df_pca, df_orig, n_clusters=3, random_state=42):
    """
    Trains a K-Means model on PCA features.
    Sorts clusters by their mean Volatility_21d (low vol -> high vol).
    """
    print("\nTraining K-Means model...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    raw_labels = kmeans.fit_predict(df_pca)
    
    # Map labels to be sorted by average Volatility_21d (low vol = 0, high vol = 2)
    vol_col = 'Volatility_21d'
    temp_df = pd.DataFrame({'label': raw_labels, 'vol': df_orig[vol_col]})
    mean_vols = temp_df.groupby('label')['vol'].mean().sort_values()
    
    # Map old labels to sorted labels
    label_map = {old_label: new_label for new_label, old_label in enumerate(mean_vols.index)}
    sorted_labels = np.array([label_map[l] for l in raw_labels])
    
    # Store label mapping inside model object for later use
    kmeans.label_map_ = label_map
    
    print(f"K-Means clusters sorted by mean volatility: {mean_vols.to_dict()}")
    return sorted_labels, kmeans

def train_gmm(df_pca, df_orig, n_components=3, random_state=42):
    """
    Trains a Gaussian Mixture Model on PCA features.
    Sorts components by their mean Volatility_21d (low vol -> high vol).
    """
    print("\nTraining Gaussian Mixture Model (GMM)...")
    gmm = GaussianMixture(n_components=n_components, random_state=random_state, n_init=5)
    gmm.fit(df_pca)
    
    # Predict probabilities and hard labels
    probs = gmm.predict_proba(df_pca)
    raw_labels = gmm.predict(df_pca)
    
    # Map components to be sorted by average Volatility_21d (low vol = 0, high vol = 2)
    vol_col = 'Volatility_21d'
    temp_df = pd.DataFrame({'label': raw_labels, 'vol': df_orig[vol_col]})
    mean_vols = temp_df.groupby('label')['vol'].mean().sort_values()
    
    # Map old labels to sorted labels
    label_map = {old_label: new_label for new_label, old_label in enumerate(mean_vols.index)}
    sorted_labels = np.array([label_map[l] for l in raw_labels])
    
    # Re-order probabilities according to sorted components
    sorted_probs = np.zeros_like(probs)
    for old_l, new_l in label_map.items():
        sorted_probs[:, new_l] = probs[:, old_l]
        
    # Store label mapping inside model object
    gmm.label_map_ = label_map
    
    print(f"GMM components sorted by mean volatility: {mean_vols.to_dict()}")
    return sorted_labels, sorted_probs, gmm

def run_clustering_pipeline(ticker="^GSPC", pca_path=None, orig_path=None, output_dir=None):
    """
    Runs K-Means and GMM, saves models and outputs.
    """
    if pca_path is None:
        safe_ticker = ticker.replace("-", "_")
        pca_path = f"data/{safe_ticker}/features_pca_robust.csv"
    if orig_path is None:
        safe_ticker = ticker.replace("-", "_")
        orig_path = f"data/{safe_ticker}/features.csv"
    if output_dir is None:
        safe_ticker = ticker.replace("-", "_")
        output_dir = f"data/{safe_ticker}"

    df_pca, df_orig = load_data(pca_path, orig_path)
    
    # 1. Train K-Means
    kmeans_labels, kmeans_model = train_kmeans(df_pca, df_orig)
    
    # 2. Train GMM
    gmm_labels, gmm_probs, gmm_model = train_gmm(df_pca, df_orig)
    
    # 3. Save Models
    safe_ticker = ticker.replace("-", "_")
    models_dir = f'models/{safe_ticker}'
    os.makedirs(models_dir, exist_ok=True)
    joblib.dump(kmeans_model, os.path.join(models_dir, 'kmeans_model.pkl'))
    joblib.dump(gmm_model, os.path.join(models_dir, 'gmm_model.pkl'))
    print(f"\nSaved trained models to {models_dir}/ directory.")
    
    # 4. Save Outputs
    df_results = pd.DataFrame(index=df_pca.index)
    df_results['Close'] = df_orig['Close']
    df_results['KMeans_Regime'] = kmeans_labels
    df_results['GMM_Regime'] = gmm_labels
    
    # Add probability columns for GMM
    for i in range(gmm_probs.shape[1]):
        df_results[f'GMM_Prob_{i}'] = gmm_probs[:, i]
        
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "baseline_regimes.csv")
    df_results.to_csv(output_path)
    print(f"Saved regime results to {output_path}")
    
    # 5. Print Regime Characteristics
    print("\n--- K-Means Regime Characteristics ---")
    for r in sorted(df_results['KMeans_Regime'].unique()):
        subset = df_orig[df_results['KMeans_Regime'] == r]
        print(f"Regime {r}: Days={len(subset)}, Mean Return={subset['Log_Return'].mean()*100:.4f}%, Mean Volatility={subset['Volatility_21d'].mean()*100:.2f}%")
        
    print("\n--- GMM Regime Characteristics ---")
    for r in sorted(df_results['GMM_Regime'].unique()):
        subset = df_orig[df_results['GMM_Regime'] == r]
        print(f"Regime {r}: Days={len(subset)}, Mean Return={subset['Log_Return'].mean()*100:.4f}%, Mean Volatility={subset['Volatility_21d'].mean()*100:.2f}%")
        
    return df_pca, df_orig, df_results

if __name__ == "__main__":
    run_clustering_pipeline()
