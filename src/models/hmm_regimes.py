import pandas as pd
import numpy as np
import os
import joblib
from hmmlearn.hmm import GaussianHMM

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

def train_hmm(df_pca, df_orig, n_components=3, random_state=42):
    """
    Trains a Gaussian Hidden Markov Model (HMM) on PCA features.
    Sorts states by their mean Volatility_21d (low vol -> high vol) for consistency.
    """
    print(f"\nTraining Gaussian HMM model with {n_components} components...")
    
    # Setup HMM
    hmm = GaussianHMM(
        n_components=n_components, 
        covariance_type="full", 
        n_iter=100, 
        random_state=random_state
    )
    
    # Fit model
    hmm.fit(df_pca)
    
    # Predict states (Viterbi path) and state probabilities
    raw_labels = hmm.predict(df_pca)
    probs = hmm.predict_proba(df_pca)
    
    # Map states to be sorted by average Volatility_21d (low vol = 0, high vol = 2)
    vol_col = 'Volatility_21d'
    temp_df = pd.DataFrame({'label': raw_labels, 'vol': df_orig[vol_col]})
    mean_vols = temp_df.groupby('label')['vol'].mean().sort_values()
    
    # Construction of permutation list: perm[new_label] = old_label
    # i.e. perm[0] is the old label index of the lowest vol state
    perm = list(mean_vols.index)
    
    # Create the label map: old_label -> new_label
    label_map = {old_label: new_label for new_label, old_label in enumerate(perm)}
    
    # Sort the model parameters in-place
    hmm.startprob_ = hmm.startprob_[perm]
    hmm.means_ = hmm.means_[perm]
    hmm.covars_ = hmm.covars_[perm]
    
    # Sort transition matrix: transmat_[old_idx, old_idx] -> permute both rows and columns
    hmm.transmat_ = hmm.transmat_[perm][:, perm]
    
    # Verify by predicting again with the sorted model
    sorted_labels = hmm.predict(df_pca)
    sorted_probs = hmm.predict_proba(df_pca)
    
    # Calculate sorted mean vols to double check
    sorted_mean_vols = pd.DataFrame({'label': sorted_labels, 'vol': df_orig[vol_col]}).groupby('label')['vol'].mean()
    
    print(f"HMM states sorted by mean volatility: {sorted_mean_vols.to_dict()}")
    return sorted_labels, sorted_probs, hmm

def run_hmm_pipeline(pca_path="data/features_pca_robust.csv", 
                     orig_path="data/features_sp500.csv", 
                     output_dir="data"):
    """
    Runs the HMM pipeline, saves the model and the outputs.
    """
    df_pca, df_orig = load_data(pca_path, orig_path)
    
    # 1. Train and Sort HMM
    hmm_labels, hmm_probs, hmm_model = train_hmm(df_pca, df_orig)
    
    # 2. Save Model
    os.makedirs('models', exist_ok=True)
    model_output_path = 'models/hmm_model.pkl'
    joblib.dump(hmm_model, model_output_path)
    print(f"Saved trained HMM model to {model_output_path}")
    
    # 3. Save Results
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
        
    # 5. Print Transition Matrix
    print("\n--- HMM Transition Probability Matrix ---")
    states = ['Regime 0 (Bull)', 'Regime 1 (Sideways)', 'Regime 2 (Bear)']
    transmat_df = pd.DataFrame(hmm_model.transmat_, index=states, columns=states)
    print(transmat_df.round(4))
    
    return df_pca, df_orig, df_results

if __name__ == "__main__":
    run_hmm_pipeline()
