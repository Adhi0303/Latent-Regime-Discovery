import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import shap

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.baseline_clustering import load_data
from src.models.evaluation import calculate_aic_bic, evaluate_clustering, get_surrogate_shap_values
from hmmlearn.hmm import GaussianHMM

def run_model_selection(pca_path="data/features_pca_robust.csv", max_regimes=5):
    """
    Evaluates HMM models with 2 to max_regimes components.
    """
    df_pca = pd.read_csv(pca_path, index_col=0, parse_dates=True)
    
    results = []
    
    print("Testing different numbers of regimes...")
    for n in range(2, max_regimes + 1):
        print(f"Training HMM with {n} regimes...")
        model = GaussianHMM(n_components=n, covariance_type="full", random_state=42, n_iter=100)
        model.fit(df_pca)
        
        labels = model.predict(df_pca)
        aic, bic = calculate_aic_bic(model, df_pca)
        sil_score = evaluate_clustering(df_pca, labels)
        
        results.append({
            'n_regimes': n,
            'AIC': aic,
            'BIC': bic,
            'Silhouette_Score': sil_score
        })
        
    df_metrics = pd.DataFrame(results)
    
    # Save metrics
    os.makedirs('data', exist_ok=True)
    metrics_path = 'data/evaluation_metrics.csv'
    df_metrics.to_csv(metrics_path, index=False)
    print(f"\nSaved evaluation metrics to {metrics_path}")
    
    return df_metrics

def plot_elbow_curve(df_metrics, output_path="notebooks/aic_bic_plot.png"):
    """
    Plots AIC and BIC to find the 'elbow' (optimal number of regimes).
    """
    plt.figure(figsize=(10, 6))
    plt.plot(df_metrics['n_regimes'], df_metrics['AIC'], marker='o', label='AIC', color='blue')
    plt.plot(df_metrics['n_regimes'], df_metrics['BIC'], marker='s', label='BIC', color='red')
    
    plt.title('HMM Model Selection: AIC & BIC Scores')
    plt.xlabel('Number of Regimes (Components)')
    plt.ylabel('Information Criterion Score (Lower is Better)')
    plt.xticks(df_metrics['n_regimes'])
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Saved AIC/BIC elbow plot to {output_path}")

def run_shap_analysis(orig_path="data/features_sp500.csv", regimes_path="data/hmm_regimes.csv"):
    """
    Loads original features and HMM labels to train a surrogate model and plot SHAP.
    """
    print("\nStarting SHAP Surrogate Analysis for 3-Regime Model...")
    df_orig = pd.read_csv(orig_path, index_col=0, parse_dates=True)
    df_regimes = pd.read_csv(regimes_path, index_col=0, parse_dates=True)
    
    # Original features (drop Close price as it's not a scaled stationary feature)
    features_to_drop = ['Close']
    X_orig = df_orig.drop(columns=[col for col in features_to_drop if col in df_orig.columns])
    
    labels = df_regimes['HMM_Regime']
    
    # Train surrogate and get SHAP values
    rf, explainer, shap_values = get_surrogate_shap_values(X_orig, labels)
    
    # Plot SHAP summary plot
    # For multi-class, shap_values is a list of arrays (one per class in older SHAP) 
    # or an array of shape (n_samples, n_features, n_classes).
    # We will use the bar plot which handles multi-class well.
    plt.figure(figsize=(12, 8))
    
    # Provide class names to the plot
    class_names = ["Regime 0 (Bull)", "Regime 1 (Sideways)", "Regime 2 (Bear)"]
    
    try:
        shap.summary_plot(shap_values, X_orig, plot_type="bar", class_names=class_names, show=False)
        
        output_path = "notebooks/shap_summary.png"
        plt.tight_layout()
        plt.savefig(output_path)
        print(f"Saved SHAP summary plot to {output_path}")
    except Exception as e:
        print(f"Could not generate SHAP plot due to: {e}")

if __name__ == "__main__":
    df_metrics = run_model_selection()
    plot_elbow_curve(df_metrics)
    run_shap_analysis()
    print("\nPhase 8 Evaluation Complete!")
