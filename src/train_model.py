import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
import os
import json

# --- Configuration ---
TIMESTEPS = 10  # How many previous data points to use to predict the next one
EPOCHS = 50
BATCH_SIZE = 32
MODEL_PATH = os.path.join('models', 'anomaly_detector.keras')
THRESHOLD_PATH = os.path.join('models', 'threshold.json')


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
    for i in range(len(data) - timesteps + 1):
        sequences.append(data.iloc[i:i + timesteps].values)
    if len(sequences) == 0:
        return np.empty((0, timesteps, data.shape[1]), dtype=np.float32)
    return np.array(sequences, dtype=np.float32)


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
    print(f"Loaded data with {scaled_df.shape[0]} rows and {scaled_df.shape[1]} features.")

    # 2. Create Sequences
    sequences = create_sequences(scaled_df, TIMESTEPS)
    if sequences.size == 0 or sequences.shape[0] < 1:
        print(f"Error: Not enough data to create any sequences with timesteps={TIMESTEPS}.")
        return

    n_sequences, _, n_features = sequences.shape
    print(f"Created {n_sequences} sequences of {TIMESTEPS} timesteps and {n_features} features.")

    # 3. Build Model
    print("\nBuilding model...")
    model = build_model(TIMESTEPS, n_features)

    # 4. Train Model
    print("\nTraining model...")
    history = model.fit(
        sequences, sequences,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_split=0.1,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, mode='min', restore_best_weights=True)
        ],
        verbose=1
    )
    print("Model training complete.")

    # 5. Save Model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save(MODEL_PATH)
    print(f"\nModel saved successfully to {MODEL_PATH}")

    # 6. Calculate and save dynamic threshold
    print("\nCalculating dynamic anomaly threshold...")
    reconstructed_sequences = model.predict(sequences, verbose=0)
    train_mae_loss = np.mean(np.abs(reconstructed_sequences - sequences), axis=(1, 2))

    # mean + 3 * std is a common starting point
    threshold = float(np.mean(train_mae_loss) + 3 * np.std(train_mae_loss))
    print(f"Calculated threshold: {threshold}")

    # Save the threshold to a JSON file for the API to load
    with open(THRESHOLD_PATH, 'w') as f:
        json.dump({"threshold": threshold}, f)
    print(f"Threshold saved to {THRESHOLD_PATH}")

    print("\n--- Model Training Finished ---")


if __name__ == '__main__':
    main()