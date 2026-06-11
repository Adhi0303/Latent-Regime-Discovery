import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.dates as mdates

# Add the project root to the python path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.models.baseline_clustering import run_clustering_pipeline

def plot_price_with_regimes(df_results, title, output_path):
    """
    Plots the S&P 500 Close price with the background shaded by the active regime.
    """
    print(f"Generating price plot: {title}...")
    fig, ax = plt.subplots(figsize=(15, 7))
    
    # Plot S&P 500 Close price (log scale to see the percentage changes better over 21 years)
    ax.plot(df_results.index, df_results['Close'], color='black', linewidth=1.2, label='S&P 500 Close')
    ax.set_yscale('log')
    
    # Colors for the regimes: 0 = Green (Bull), 1 = Orange (Sideways), 2 = Red (Bear/Crash)
    regime_colors = {
        0: 'lightgreen',
        1: 'gold',
        2: 'tomato'
    }
    
    regime_labels = {
        0: 'Regime 0 (Low Vol / Bull)',
        1: 'Regime 1 (Med Vol / Sideways)',
        2: 'Regime 2 (High Vol / Bear)'
    }
    
    # Shade the background based on the regime
    # We find contiguous blocks of the same regime to make plotting faster
    regime_series = df_results[df_results.columns[1]] # Either KMeans_Regime or GMM_Regime
    
    # Group by contiguous values
    change_points = (regime_series != regime_series.shift()).cumsum()
    blocks = df_results.groupby(change_points)
    
    # Track which labels we have added to the legend to avoid duplicates
    added_to_legend = set()
    
    for _, block in blocks:
        start_date = block.index[0]
        end_date = block.index[-1]
        regime = block[regime_series.name].iloc[0]
        
        color = regime_colors[regime]
        label = regime_labels[regime] if regime not in added_to_legend else ""
        if label:
            added_to_legend.add(regime)
            
        ax.axvspan(start_date, end_date, color=color, alpha=0.3, label=label)
        
    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('S&P 500 Price (Log Scale)', fontsize=12)
    ax.grid(True, which="both", ls="--", alpha=0.5)
    
    # Format x-axis dates
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    # Place legend
    ax.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Saved price plot to {output_path}")
    plt.close()

def plot_gmm_probabilities(df_results, output_path):
    """
    Plots the daily probabilities of each regime over time.
    """
    print("Generating GMM probabilities plot...")
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(15, 10), sharex=True)
    fig.suptitle('GMM Regime Probabilities Over Time', fontsize=16)
    
    colors = ['green', 'orange', 'red']
    labels = ['Regime 0 (Low Vol / Bull)', 'Regime 1 (Med Vol / Sideways)', 'Regime 2 (High Vol / Bear)']
    
    for i in range(3):
        axes[i].plot(df_results.index, df_results[f'GMM_Prob_{i}'], color=colors[i], linewidth=0.8, alpha=0.8)
        axes[i].fill_between(df_results.index, 0, df_results[f'GMM_Prob_{i}'], color=colors[i], alpha=0.2)
        axes[i].set_ylabel('Probability', fontsize=10)
        axes[i].set_ylim(0, 1.05)
        axes[i].grid(True, ls="--", alpha=0.5)
        axes[i].legend([labels[i]], loc='upper right')
        
    axes[-1].set_xlabel('Date', fontsize=12)
    
    # Format x-axis dates
    axes[-1].xaxis.set_major_locator(mdates.YearLocator(2))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    plt.savefig(output_path, dpi=300)
    print(f"Saved probabilities plot to {output_path}")
    plt.close()

def plot_regime_characteristics(df_orig, df_results, output_path):
    """
    Plots a bar chart comparing the mean Return and Volatility of each regime.
    """
    print("Generating regime characteristics plot...")
    
    # Add regime columns to df_orig temporarily for calculations
    temp_df = df_orig.copy()
    temp_df['KMeans_Regime'] = df_results['KMeans_Regime']
    temp_df['GMM_Regime'] = df_results['GMM_Regime']
    
    # Calculate stats
    kmeans_stats = temp_df.groupby('KMeans_Regime').agg({
        'Log_Return': lambda x: x.mean() * 100, # Mean return in %
        'Volatility_21d': lambda x: x.mean() * 100 # Mean vol in %
    }).rename(columns={'Log_Return': 'Mean Return (%)', 'Volatility_21d': 'Mean Volatility (%)'})
    
    gmm_stats = temp_df.groupby('GMM_Regime').agg({
        'Log_Return': lambda x: x.mean() * 100,
        'Volatility_21d': lambda x: x.mean() * 100
    }).rename(columns={'Log_Return': 'Mean Return (%)', 'Volatility_21d': 'Mean Volatility (%)'})
    
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 10))
    fig.suptitle('Regime Characteristics Comparison', fontsize=16)
    
    colors = ['lightgreen', 'orange', 'tomato']
    
    # K-Means Return
    sns.barplot(x=kmeans_stats.index, y='Mean Return (%)', data=kmeans_stats, ax=axes[0, 0], palette=colors)
    axes[0, 0].set_title('K-Means: Mean Daily Return (%)')
    axes[0, 0].set_xlabel('Regime')
    
    # K-Means Volatility
    sns.barplot(x=kmeans_stats.index, y='Mean Volatility (%)', data=kmeans_stats, ax=axes[0, 1], palette=colors)
    axes[0, 1].set_title('K-Means: Mean Annual Volatility (%)')
    axes[0, 1].set_xlabel('Regime')
    
    # GMM Return
    sns.barplot(x=gmm_stats.index, y='Mean Return (%)', data=gmm_stats, ax=axes[1, 0], palette=colors)
    axes[1, 0].set_title('GMM: Mean Daily Return (%)')
    axes[1, 0].set_xlabel('Regime')
    
    # GMM Volatility
    sns.barplot(x=gmm_stats.index, y='Mean Volatility (%)', data=gmm_stats, ax=axes[1, 1], palette=colors)
    axes[1, 1].set_title('GMM: Mean Annual Volatility (%)')
    axes[1, 1].set_xlabel('Regime')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    plt.savefig(output_path, dpi=300)
    print(f"Saved characteristics plot to {output_path}")
    plt.close()

def main():
    # Set correct working directories depending on script execution context
    current_dir = os.path.basename(os.getcwd())
    if current_dir == "notebooks":
        pca_file = "../data/features_pca_robust.csv"
        orig_file = "../data/features_sp500.csv"
        out_data_dir = "../data"
        out_plot_dir = "."
        # Make sure we don't mess up relative imports
        os.chdir("..")
        pca_file = "data/features_pca_robust.csv"
        orig_file = "data/features_sp500.csv"
        out_data_dir = "data"
        out_plot_dir = "notebooks"
    else:
        pca_file = "data/features_pca_robust.csv"
        orig_file = "data/features_sp500.csv"
        out_data_dir = "data"
        out_plot_dir = "notebooks"
        os.makedirs(out_plot_dir, exist_ok=True)
        
    # Run pipeline
    df_pca, df_orig, df_results = run_clustering_pipeline(pca_file, orig_file, out_data_dir)
    
    # Generate Plots
    plot_price_with_regimes(
        df_results[['Close', 'KMeans_Regime']], 
        "S&P 500 Historical Price Colored by K-Means Regimes", 
        os.path.join(out_plot_dir, "kmeans_regimes.png")
    )
    
    plot_price_with_regimes(
        df_results[['Close', 'GMM_Regime']], 
        "S&P 500 Historical Price Colored by GMM Regimes (Most Probable)", 
        os.path.join(out_plot_dir, "gmm_regimes.png")
    )
    
    plot_gmm_probabilities(df_results, os.path.join(out_plot_dir, "gmm_probabilities.png"))
    
    plot_regime_characteristics(df_orig, df_results, os.path.join(out_plot_dir, "regime_characteristics.png"))
    
    print("\nPhase 6 Clustering and Visualization completed successfully!")

if __name__ == "__main__":
    main()
