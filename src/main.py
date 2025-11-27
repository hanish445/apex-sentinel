import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import tensorflow as tf
import pickle
import os
import json
from typing import List

from data_collection import collect_telemetry_data
from anomaly_analysis import generate_anomaly_explanation_text

# --- Configuration ---
MODEL_PATH = os.path.join('models', 'anomaly_detector.keras')
SCALER_PATH = os.path.join('models', 'scaler.pkl')
THRESHOLD_PATH = os.path.join('models', 'threshold.json')
TIMESTEPS = 10

# --- FastAPI App Initialization ---
app = FastAPI(title="F1 Anomaly Detection API with Explanations", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class DataRequest(BaseModel):
    year: int
    gp: str
    session: str
    driver: str

@app.post("/load_data")
def load_race_data(req: DataRequest):
    """Downloads data via FastF1 and returns it as JSON to React"""
    try:
        df, error = collect_telemetry_data(req.year, req.gp, req.session, req.driver)
        if error:
            raise HTTPException(status_code=400, detail=error)

        # Convert dataframe to list of dicts for JSON response
        # Handle boolean/numpy types
        if 'Brake' in df.columns and df['Brake'].dtype == 'bool':
            df['Brake'] = df['Brake'].astype(int)

        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "API is running"}

@app.post("/predict", tags=["Anomaly Detection"])
def predict_anomaly(data: TelemetryData):
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

    # Per-sequence per-feature error (mean over timesteps for each feature)
    per_feature_error = np.mean(np.abs(sequences - reconstructed_sequences), axis=1)

    # Sequence end indices (index in original input that corresponds to end of each sequence)
    sequence_end_indices = [i + TIMESTEPS - 1 for i in range(len(sequences))]

    # Decide anomalies using loaded threshold
    anomalies = reconstruction_error > threshold

    # --- MODIFIED SECTION START ---
    feature_errors_list = []
    top_features_list = []
    explanations_list = [] # <--- NEW LIST FOR TEXT EXPLANATIONS

    # We use enumerate(per_feature_error) to get the index 'i'
    for i, seq_err in enumerate(per_feature_error):
        # 1. Build Feature Error Map
        feature_error_map = {feature_names[j]: float(seq_err[j]) for j in range(len(feature_names))}
        feature_errors_list.append(feature_error_map)

        # 2. Sort to find Top Features
        sorted_feats = sorted(feature_error_map.items(), key=lambda kv: kv[1], reverse=True)
        top_3_features = [(k, v) for k, v in sorted_feats[:3]]
        top_features_list.append(top_3_features)

        # 3. Generate Explanation Text (Backend Logic)
        explanation = ""
        if anomalies[i]: # Only generate text if it IS an anomaly
            anomaly_report = {
                "sequence_index": int(i),
                "end_index": int(sequence_end_indices[i]),
                "threshold": float(threshold),
                "reconstruction_error": float(reconstruction_error[i]),
                "top_features": top_3_features,
                "feature_errors": feature_error_map
            }
            # This calls your custom logic to generate the text
            explanation = generate_anomaly_explanation_text(anomaly_report)

        explanations_list.append(explanation)
    # --- MODIFIED SECTION END ---

    return {
        "reconstruction_error": reconstruction_error.tolist(),
        "is_anomaly": anomalies.tolist(),
        "threshold": float(threshold),
        "sequence_end_indices": sequence_end_indices,
        "feature_errors": feature_errors_list,
        "top_features": top_features_list,
        "explanations": explanations_list  # <--- RETURN THE TEXT
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)