import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import joblib

# Add the project root to the python path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.models.hmm_regimes import run_hmm_pipeline

def plot_price_with_regimes(df_results, title, output_path):
    """
    Plots the S&P 500 Close price with the background shaded by the active HMM regime.
    """
    print(f"Generating price plot: {title}...")
    fig, ax = plt.subplots(figsize=(15, 7))
    
    # Plot S&P 500 Close price on a log scale
    ax.plot(df_results.index, df_results['Close'], color='black', linewidth=1.2, label='S&P 500 Close')
    ax.set_yscale('log')
    
    # Colors matching the baseline clustering visualization
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
    
    regime_series = df_results['HMM_Regime']
    
    # Group by contiguous values to plot faster
    change_points = (regime_series != regime_series.shift()).cumsum()
    blocks = df_results.groupby(change_points)
    
    added_to_legend = set()
    
    for _, block in blocks:
        start_date = block.index[0]
        end_date = block.index[-1]
        regime = block['HMM_Regime'].iloc[0]
        
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
    
    ax.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Saved price plot to {output_path}")
    plt.close()

def plot_hmm_probabilities(df_results, output_path):
    """
    Plots the daily HMM state probabilities over time.
    """
    print("Generating HMM probabilities plot...")
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(15, 10), sharex=True)
    fig.suptitle('HMM Regime Probabilities Over Time', fontsize=16)
    
    colors = ['green', 'orange', 'red']
    labels = ['Regime 0 (Low Vol / Bull)', 'Regime 1 (Med Vol / Sideways)', 'Regime 2 (High Vol / Bear)']
    
    for i in range(3):
        axes[i].plot(df_results.index, df_results[f'HMM_Prob_{i}'], color=colors[i], linewidth=0.8, alpha=0.8)
        axes[i].fill_between(df_results.index, 0, df_results[f'HMM_Prob_{i}'], color=colors[i], alpha=0.2)
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

def plot_transition_matrix(transmat, output_path):
    """
    Plots a heatmap of the state transition probabilities.
    """
    print("Generating transition matrix heatmap...")
    fig, ax = plt.subplots(figsize=(8, 6))
    
    states = ['Regime 0\n(Bull)', 'Regime 1\n(Sideways)', 'Regime 2\n(Bear)']
    
    sns.heatmap(
        transmat, 
        annot=True, 
        fmt=".4f", 
        cmap="Blues", 
        xticklabels=states, 
        yticklabels=states,
        cbar=True,
        ax=ax,
        annot_kws={"size": 12}
    )
    
    ax.set_title("HMM Transition Probability Matrix", fontsize=14, pad=15)
    ax.set_ylabel("From Regime", fontsize=12)
    ax.set_xlabel("To Regime", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Saved transition matrix plot to {output_path}")
    plt.close()

def plot_regime_characteristics(df_orig, df_results, output_path):
    """
    Plots a bar chart comparing the mean Return and Volatility of each HMM regime.
    """
    print("Generating regime characteristics plot...")
    
    temp_df = df_orig.copy()
    temp_df['HMM_Regime'] = df_results['HMM_Regime']
    
    stats = temp_df.groupby('HMM_Regime').agg({
        'Log_Return': lambda x: x.mean() * 100,
        'Volatility_21d': lambda x: x.mean() * 100
    }).rename(columns={'Log_Return': 'Mean Return (%)', 'Volatility_21d': 'Mean Volatility (%)'})
    
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 5))
    fig.suptitle('HMM Regime Characteristics Comparison', fontsize=16)
    
    colors = ['lightgreen', 'orange', 'tomato']
    
    # Return
    sns.barplot(x=stats.index, y='Mean Return (%)', data=stats, ax=axes[0], palette=colors)
    axes[0].set_title('Mean Daily Return (%)')
    axes[0].set_xlabel('Regime')
    
    # Volatility
    sns.barplot(x=stats.index, y='Mean Volatility (%)', data=stats, ax=axes[1], palette=colors)
    axes[1].set_title('Mean Annual Volatility (%)')
    axes[1].set_xlabel('Regime')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)
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
        
    # Run HMM pipeline
    df_pca, df_orig, df_results = run_hmm_pipeline(pca_file, orig_file, out_data_dir)
    
    # Load HMM model to extract transition matrix
    hmm_model = joblib.load('models/hmm_model.pkl')
    
    # Generate Plots
    plot_price_with_regimes(
        df_results[['Close', 'HMM_Regime']], 
        "S&P 500 Historical Price Colored by HMM Regimes", 
        os.path.join(out_plot_dir, "hmm_regimes.png")
    )
    
    plot_hmm_probabilities(df_results, os.path.join(out_plot_dir, "hmm_probabilities.png"))
    
    plot_transition_matrix(hmm_model.transmat_, os.path.join(out_plot_dir, "hmm_transition_matrix.png"))
    
    plot_regime_characteristics(df_orig, df_results, os.path.join(out_plot_dir, "hmm_regime_characteristics.png"))
    
    print("\nPhase 7 HMM Modeling and Visualization completed successfully!")

if __name__ == "__main__":
    main()
