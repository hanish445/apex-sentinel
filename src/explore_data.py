import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.preprocessing import MinMaxScaler

def explore_and_preprocess_data():
    """
    Loads, visualizes, and preprocesses the F1 telemetry data.
    """
    print("--- Starting Data Exploration and Preprocessing ---")

    # --- 1. Load Data ---
    data_path = os.path.join('data', 'telemetry_data.csv')
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        print("Please run 'python src/data_collection.py' first.")
        return

    df = pd.read_csv(data_path)
    print("Dataset loaded successfully.")
    print("\nFirst 5 rows of the dataset:")
    print(df.head())
    print("\nDataset Info:")
    df.info()

    # --- 2. Visualize Data ---
    print("\nGenerating and saving telemetry plots...")
    channels_to_plot = ['Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS']
    
    fig, axes = plt.subplots(len(channels_to_plot), 1, figsize=(15, 12), sharex=True)
    fig.suptitle('Key Telemetry Channels over Lap Distance', fontsize=16)

    for i, channel in enumerate(channels_to_plot):
        axes[i].plot(df['Distance'], df[channel], label=channel)
        axes[i].set_ylabel(channel)
        axes[i].legend(loc='upper right')
    
    axes[-1].set_xlabel('Distance (meters)')
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    
    # Create directory for saving plots if it doesn't exist
    figures_dir = os.path.join('reports', 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    
    plot_path = os.path.join(figures_dir, 'telemetry_visualization.png')
    plt.savefig(plot_path)
    print(f"Plots saved to {plot_path}")
    plt.close() # Close the plot to free up memory

    # --- 3. Preprocess Data ---
    print("\nPreprocessing data for the model...")
    features = ['Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS']
    model_df = df[features].copy()

    if model_df['Brake'].dtype == 'bool':
        model_df['Brake'] = model_df['Brake'].astype(int)

    # Scale features to be between 0 and 1
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(model_df)
    scaled_df = pd.DataFrame(scaled_data, columns=features)
    
    print("Data successfully scaled.")
    print("\nFirst 5 rows of scaled data:")
    print(scaled_df.head())

    # Save the scaled data for the next phase
    scaled_data_path = os.path.join('data', 'scaled_telemetry_data.csv')
    scaled_df.to_csv(scaled_data_path, index=False)
    print(f"\nScaled data saved to {scaled_data_path}")
    
    print("\n--- Data Exploration and Preprocessing Finished ---")


if __name__ == '__main__':
    explore_and_preprocess_data()