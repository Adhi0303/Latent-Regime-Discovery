import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy.stats import skew, kurtosis

def run_eda(input_path="../data/features_sp500.csv", output_dir="."):
    print(f"Loading features from {input_path}...")
    df = pd.read_csv(input_path, index_col='Date', parse_dates=True)
    
    # We drop 'Close' because it is non-stationary and only kept for charting
    features = df.drop(columns=['Close'])
    
    # ---------------------------------------------------------
    # 1. Statistical Summary (Mean, Std, Skewness, Kurtosis)
    # ---------------------------------------------------------
    print("\n--- Feature Statistical Summary ---")
    stats = pd.DataFrame({
        'Mean': features.mean(),
        'Std Dev': features.std(),
        'Skewness': features.apply(skew),
        'Kurtosis': features.apply(kurtosis)
    })
    print(stats.round(4))
    
    # ---------------------------------------------------------
    # 2. Plotting Distributions (Histograms)
    # ---------------------------------------------------------
    print("\nGenerating feature distributions plot...")
    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(15, 12))
    fig.suptitle('Feature Distributions', fontsize=16)
    axes = axes.flatten()
    
    for i, col in enumerate(features.columns):
        sns.histplot(features[col], bins=50, kde=True, ax=axes[i], color='royalblue')
        axes[i].set_title(f'Distribution of {col}')
        axes[i].set_xlabel('')
        axes[i].set_ylabel('Frequency')
        
    # Hide any unused subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
        
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    dist_path = os.path.join(output_dir, "feature_distributions.png")
    plt.savefig(dist_path, dpi=300)
    print(f"Saved distributions plot to {dist_path}")
    plt.close()
    
    # ---------------------------------------------------------
    # 3. Correlation Matrix Heatmap
    # ---------------------------------------------------------
    print("\nGenerating correlation matrix heatmap...")
    corr = features.corr()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", vmin=-1, vmax=1, linewidths=0.5)
    plt.title('Feature Correlation Matrix', fontsize=14)
    plt.tight_layout()
    
    corr_path = os.path.join(output_dir, "correlation_heatmap.png")
    plt.savefig(corr_path, dpi=300)
    print(f"Saved correlation heatmap to {corr_path}")
    plt.close()
    
    print("\nEDA completed successfully.")

if __name__ == "__main__":
    # Ensure we run correctly if executed from root or notebooks directory
    current_dir = os.path.basename(os.getcwd())
    if current_dir == "notebooks":
        input_file = "../data/features_sp500.csv"
        out_dir = "."
    else:
        input_file = "data/features_sp500.csv"
        out_dir = "notebooks"
        os.makedirs(out_dir, exist_ok=True)
        
    run_eda(input_path=input_file, output_dir=out_dir)
