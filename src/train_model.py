import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
import os

# --- Configuration ---
TIMESTEPS = 10  # How many previous data points to use to predict the next one
EPOCHS = 50
BATCH_SIZE = 32
MODEL_PATH = os.path.join('models', 'anomaly_detector.keras')

def load_data(filepath):
    """Loads the preprocessed data."""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        print("Please run 'python src/explore_data.py' first.")
        return None
    return pd.read_csv(filepath)

def create_sequences(data, timesteps):
    """Converts a time-series dataframe into 3D sequences for LSTM."""
    sequences = []
    for i in range(len(data) - timesteps):
        sequences.append(data.iloc[i:i + timesteps].values)
    return np.array(sequences)

def build_model(timesteps, n_features):
    """Builds and compiles the LSTM autoencoder model."""
    model = Sequential()
    # Encoder
    model.add(LSTM(128, activation='relu', input_shape=(timesteps, n_features), return_sequences=False))
    model.add(RepeatVector(timesteps))
    # Decoder
    model.add(LSTM(128, activation='relu', return_sequences=True))
    model.add(TimeDistributed(Dense(n_features)))
    
    model.compile(optimizer='adam', loss='mae')
    model.summary()
    return model

def main():
    """Main function to run the model training pipeline."""
    print("--- Starting Model Training ---")

    # 1. Load Data
    data_path = os.path.join('data', 'scaled_telemetry_data.csv')
    scaled_df = load_data(data_path)
    if scaled_df is None:
        return
    print(f"Loaded data with {scaled_df.shape[0]} samples and {scaled_df.shape[1]} features.")

    # 2. Create Sequences
    sequences = create_sequences(scaled_df, TIMESTEPS)
    n_sequences, _, n_features = sequences.shape
    print(f"Created {n_sequences} sequences of {TIMESTEPS} timesteps and {n_features} features.")

    # 3. Build Model
    print("\nBuilding model...")
    model = build_model(TIMESTEPS, n_features)

    # 4. Train Model
    # The model learns to reconstruct the input sequences.
    print("\nTraining model...")
    history = model.fit(
        sequences, sequences,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_split=0.1,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, mode='min')
        ]
    )
    print("Model training complete.")

    # 5. Save Model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save(MODEL_PATH)
    print(f"\nModel saved successfully to {MODEL_PATH}")
    
    print("\n--- Model Training Finished ---")

if __name__ == '__main__':
    main()