import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Add the project root to the python path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.features.preprocessing import run_preprocessing_pipeline

def plot_scaling_comparison(df_orig, df_std, df_robust, output_dir="."):
    """
    Plots histograms comparing Original vs StandardScaler vs RobustScaler.
    """
    print("\nGenerating scaling comparison plot...")
    features = df_orig.columns
    n_features = len(features)
    
    fig, axes = plt.subplots(nrows=n_features, ncols=3, figsize=(15, 4 * n_features))
    fig.suptitle('Feature Scaling Comparison', fontsize=16)
    
    for i, feature in enumerate(features):
        # Original
        sns.histplot(df_orig[feature], bins=50, kde=True, ax=axes[i, 0], color='gray')
        axes[i, 0].set_title(f'Original: {feature}')
        
        # Standard Scaled
        sns.histplot(df_std[feature], bins=50, kde=True, ax=axes[i, 1], color='blue')
        axes[i, 1].set_title(f'Standard Scaled: {feature}')
        
        # Robust Scaled
        sns.histplot(df_robust[feature], bins=50, kde=True, ax=axes[i, 2], color='green')
        axes[i, 2].set_title(f'Robust Scaled: {feature}')
        
    plt.tight_layout()
    plt.subplots_adjust(top=0.95)
    
    out_path = os.path.join(output_dir, "scaling_comparison.png")
    plt.savefig(out_path, dpi=300)
    print(f"Saved scaling comparison to {out_path}")
    plt.close()

def plot_pca_variance(pca_model, output_dir="."):
    """
    Plots the explained variance ratio and cumulative variance of PCA.
    """
    print("\nGenerating PCA variance plot...")
    
    # Calculate cumulative variance
    explained_variance = pca_model.explained_variance_ratio_
    cumulative_variance = np.cumsum(explained_variance)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Bar chart for individual variance
    bars = ax.bar(range(1, len(explained_variance) + 1), explained_variance, alpha=0.7, align='center',
                  label='Individual explained variance', color='royalblue')
    
    # Step plot for cumulative variance
    ax.step(range(1, len(cumulative_variance) + 1), cumulative_variance, where='mid',
            label='Cumulative explained variance', color='darkorange', linewidth=2)
            
    ax.set_ylabel('Explained Variance Ratio')
    ax.set_xlabel('Principal Component Index')
    ax.set_title('PCA Explained Variance (Robust Scaled Data)')
    
    # Set x-ticks explicitly to be integers
    ax.set_xticks(range(1, len(explained_variance) + 1))
    
    ax.legend(loc='best')
    plt.tight_layout()
    
    out_path = os.path.join(output_dir, "pca_variance.png")
    plt.savefig(out_path, dpi=300)
    print(f"Saved PCA variance plot to {out_path}")
    plt.close()

def plot_pca_2d_projection(df_pca, output_dir="."):
    """
    Plots the first two Principal Components as a scatter plot.
    """
    print("\nGenerating PCA 2D projection plot...")
    
    if df_pca.shape[1] < 2:
        print("Not enough PCA components to plot 2D projection.")
        return
        
    plt.figure(figsize=(10, 8))
    # We use a scatter plot with slight transparency to see density
    plt.scatter(df_pca['PC1'], df_pca['PC2'], alpha=0.4, c='purple', s=10)
    
    plt.title('2D PCA Projection of Market Regimes Space')
    plt.xlabel('Principal Component 1 (PC1)')
    plt.ylabel('Principal Component 2 (PC2)')
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Add axv/axh lines at 0
    plt.axhline(0, color='black', linewidth=0.8, linestyle='-')
    plt.axvline(0, color='black', linewidth=0.8, linestyle='-')
    
    plt.tight_layout()
    
    out_path = os.path.join(output_dir, "pca_2d_projection.png")
    plt.savefig(out_path, dpi=300)
    print(f"Saved PCA 2D projection plot to {out_path}")
    plt.close()

def main():
    # Ensure paths are correct depending on where the script is run
    current_dir = os.path.basename(os.getcwd())
    if current_dir == "notebooks":
        input_file = "../data/features_sp500.csv"
        out_data_dir = "../data"
        out_plot_dir = "."
        # For models directory in run_preprocessing_pipeline
        os.chdir("..") 
        input_file = "data/features_sp500.csv"
        out_data_dir = "data"
        out_plot_dir = "notebooks"
    else:
        input_file = "data/features_sp500.csv"
        out_data_dir = "data"
        out_plot_dir = "notebooks"
        os.makedirs(out_plot_dir, exist_ok=True)
        
    # Run the pipeline
    df_orig, df_std, df_robust, df_pca, pca_model = run_preprocessing_pipeline(
        input_path=input_file, 
        output_dir=out_data_dir
    )
    
    # Generate Plots
    plot_scaling_comparison(df_orig, df_std, df_robust, output_dir=out_plot_dir)
    plot_pca_variance(pca_model, output_dir=out_plot_dir)
    plot_pca_2d_projection(df_pca, output_dir=out_plot_dir)
    
    print("\nPhase 5 Preprocessing and Visualization completed successfully!")

if __name__ == "__main__":
    main()
