import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
import tensorflow as tf
import pickle
import os
import json
from typing import List

# --- Configuration ---
MODEL_PATH = os.path.join('models', 'anomaly_detector.keras')
SCALER_PATH = os.path.join('models', 'scaler.pkl')
THRESHOLD_PATH = os.path.join('models', 'threshold.json')
TIMESTEPS = 10

# --- FastAPI App Initialization ---
app = FastAPI(title="F1 Anomaly Detection API with Explanations", version="1.1.0")

# --- Load Model, Scaler, and Threshold at Startup ---
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    with open(THRESHOLD_PATH, 'r') as f:
        threshold_data = json.load(f)
        threshold = float(threshold_data['threshold'])
    print("Model, scaler, and dynamic threshold loaded successfully.")
    print(f"Using anomaly threshold: {threshold}")
except Exception as e:
    print(f"Error loading model, scaler, or threshold: {e}")
    model, scaler, threshold = None, None, None

# --- Define Request Body Structure ---
class TelemetryData(BaseModel):
    Speed: List[float]
    RPM: List[float]
    Throttle: List[float]
    Brake: List[float]
    nGear: List[float]
    DRS: List[float]

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "API is running"}

@app.post("/predict", tags=["Anomaly Detection"])
def predict_anomaly(data: TelemetryData):
    """
    Receives telemetry data (lists for each feature), constructs sliding windows of length TIMESTEPS,
    predicts reconstructions, and returns:
      - reconstruction_error (per-sequence scalar)
      - is_anomaly (per-sequence boolean)
      - threshold (used)
      - sequence_end_indices (index in original input for each sequence's end)
      - feature_errors (list of per-sequence dicts mapping feature -> mean MAE over timesteps)
      - top_features (list of lists with top contributing features for each sequence)
    """
    if not all([model is not None, scaler is not None, threshold is not None]):
        return {"error": "Model, scaler, or threshold not loaded. Check server logs."}

    # Build DataFrame from input lists
    input_dict = data.dict()
    input_df = pd.DataFrame(input_dict)
    feature_names = list(input_df.columns)

    if len(input_df) < TIMESTEPS:
        return {"error": f"Not enough data provided. Need at least {TIMESTEPS} timesteps."}

    # Scale using the saved scaler
    try:
        scaled_data = scaler.transform(input_df)
    except Exception as e:
        return {"error": f"Scaler transform failed: {e}"}

    # Create sliding sequences: shape (num_sequences, TIMESTEPS, n_features)
    sequences = np.array([scaled_data[i:i + TIMESTEPS] for i in range(len(scaled_data) - TIMESTEPS + 1)], dtype=np.float32)
    if sequences.size == 0:
        return {"error": "Could not create any sequences from the provided data."}

    # Predict reconstructions
    try:
        reconstructed_sequences = model.predict(sequences, verbose=0)
    except Exception as e:
        return {"error": f"Model prediction failed: {e}"}

    # Scalar reconstruction error per sequence (mean over timesteps and features)
    reconstruction_error = np.mean(np.abs(sequences - reconstructed_sequences), axis=(1, 2))

    # Per-sequence per-feature error (mean over timesteps for each feature) -> shape (num_sequences, n_features)
    per_feature_error = np.mean(np.abs(sequences - reconstructed_sequences), axis=1)

    # Sequence end indices (index in original input that corresponds to end of each sequence)
    sequence_end_indices = [i + TIMESTEPS - 1 for i in range(len(sequences))]

    # Decide anomalies using loaded threshold
    anomalies = reconstruction_error > threshold

    # Build readable outputs: feature_errors list and top_features list
    feature_errors_list = []
    top_features_list = []
    for seq_err in per_feature_error:
        feature_error_map = {feature_names[i]: float(seq_err[i]) for i in range(len(feature_names))}
        feature_errors_list.append(feature_error_map)
        # Sort features by error descending and take top 3
        sorted_feats = sorted(feature_error_map.items(), key=lambda kv: kv[1], reverse=True)
        top_features_list.append([(k, v) for k, v in sorted_feats[:3]])

    return {
        "reconstruction_error": reconstruction_error.tolist(),
        "is_anomaly": anomalies.tolist(),
        "threshold": float(threshold),
        "sequence_end_indices": sequence_end_indices,
        "feature_errors": feature_errors_list,
        "top_features": top_features_list
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)