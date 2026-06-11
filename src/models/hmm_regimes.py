import pandas as pd
import numpy as np
import os
import joblib
from hmmlearn.hmm import GaussianHMM
from src.models.baseline_clustering import load_data

def train_hmm(df_pca, df_orig, n_components=3, random_state=42):
    """
    Trains a Gaussian Hidden Markov Model on PCA features.
    Sorts hidden states by their mean Volatility_21d (low vol -> high vol).
    """
    print("\nTraining Hidden Markov Model (HMM)...")
    
    # GaussianHMM expects array-like of shape (n_samples, n_features)
    # We use full covariance matrix to capture feature interactions
    hmm_model = GaussianHMM(n_components=n_components, 
                            covariance_type="full", 
                            random_state=random_state, 
                            n_iter=100)
    
    hmm_model.fit(df_pca)
    
    # Predict hidden states and their probabilities
    raw_labels = hmm_model.predict(df_pca)
    probs = hmm_model.predict_proba(df_pca)
    
    # Map hidden states to be sorted by average Volatility_21d 
    # (low vol = 0 [Bull], high vol = 2 [Bear/Crisis])
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
        
    # Re-order transition matrix
    old_transmat = hmm_model.transmat_
    sorted_transmat = np.zeros_like(old_transmat)
    for old_i, new_i in label_map.items():
        for old_j, new_j in label_map.items():
            sorted_transmat[new_i, new_j] = old_transmat[old_i, old_j]
            
    # Store mappings and sorted objects inside model
    hmm_model.label_map_ = label_map
    hmm_model.sorted_transmat_ = sorted_transmat
    
    print(f"HMM hidden states sorted by mean volatility: {mean_vols.to_dict()}")
    return sorted_labels, sorted_probs, hmm_model

def run_hmm_pipeline(ticker="^GSPC", pca_path=None, orig_path=None, output_dir=None):
    """
    Runs HMM training, saves the model and the state predictions.
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
    
    # 1. Train HMM
    hmm_labels, hmm_probs, hmm_model = train_hmm(df_pca, df_orig)
      
    # 2. Save Model
    safe_ticker = ticker.replace("-", "_")
    models_dir = f'models/{safe_ticker}'
    os.makedirs(models_dir, exist_ok=True)
    model_path = f'{models_dir}/hmm_model.pkl'
    joblib.dump(hmm_model, model_path)
    print(f"\nSaved trained HMM model to {model_path}")
    
    # 3. Save Outputs
    df_results = pd.DataFrame(index=df_pca.index)
    df_results['Close'] = df_orig['Close']
    df_results['HMM_Regime'] = hmm_labels
    
    # Add probability columns
    for i in range(hmm_probs.shape[1]):
        df_results[f'HMM_Prob_{i}'] = hmm_probs[:, i]
        
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "hmm_regimes.csv")
    df_results.to_csv(output_path)
    print(f"Saved HMM regime results to {output_path}")
    
    # 4. Print Regime Characteristics
    print("\n--- HMM Regime Characteristics ---")
    for r in sorted(df_results['HMM_Regime'].unique()):
        subset = df_orig[df_results['HMM_Regime'] == r]
        print(f"Regime {r}: Days={len(subset)}, Mean Return={subset['Log_Return'].mean()*100:.4f}%, Mean Volatility={subset['Volatility_21d'].mean()*100:.2f}%")
        
    print("\n--- Transition Matrix (Sorted) ---")
    print("Rows: From Regime | Cols: To Regime")
    print(np.round(hmm_model.sorted_transmat_, 3))
    
    return df_pca, df_orig, df_results, hmm_model

if __name__ == "__main__":
    run_hmm_pipeline()
