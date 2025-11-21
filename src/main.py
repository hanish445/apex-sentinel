import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
import tensorflow as tf
import pickle
import os
import json

# --- Configuration ---
MODEL_PATH = os.path.join('models', 'anomaly_detector.keras')
SCALER_PATH = os.path.join('models', 'scaler.pkl')
THRESHOLD_PATH = os.path.join('models', 'threshold.json')  # <-- Path for the threshold file
TIMESTEPS = 10

# --- FastAPI App Initialization ---
app = FastAPI(title="F1 Anomaly Detection API", version="1.0.0")

# --- Load Model, Scaler, and Threshold at Startup ---
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    with open(THRESHOLD_PATH, 'r') as f:
        threshold_data = json.load(f)
        threshold = threshold_data['threshold']  # <-- Load the threshold value
    print("Model, scaler, and dynamic threshold loaded successfully.")
    print(f"Using anomaly threshold: {threshold}")
except Exception as e:
    print(f"Error loading model, scaler, or threshold: {e}")
    model, scaler, threshold = None, None, None


# --- Define Request Body Structure ---
class TelemetryData(BaseModel):
    Speed: list[float];
    RPM: list[float];
    Throttle: list[float];
    Brake: list[float];
    nGear: list[float];
    DRS: list[float]


# --- API Endpoints ---
@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "API is running"}


@app.post("/predict", tags=["Anomaly Detection"])
def predict_anomaly(data: TelemetryData):
    if not all([model, scaler, threshold is not None]):
        return {"error": "Model, scaler, or threshold not loaded. Check server logs."}

    input_df = pd.DataFrame(data.dict())
    if len(input_df) < TIMESTEPS:
        return {"error": f"Not enough data provided. Need at least {TIMESTEPS} timesteps."}

    scaled_data = scaler.transform(input_df)
    sequences = np.array([scaled_data[i:i + TIMESTEPS] for i in range(len(scaled_data) - TIMESTEPS + 1)])

    if len(sequences) == 0:
        return {"error": "Could not create any sequences from the provided data."}

    reconstructed_sequences = model.predict(sequences)
    reconstruction_error = np.mean(np.abs(sequences - reconstructed_sequences), axis=(1, 2))

    # Use the loaded threshold instead of a hard-coded value
    anomalies = reconstruction_error > threshold

    return {
        "reconstruction_error": reconstruction_error.tolist(),
        "is_anomaly": anomalies.tolist(),
        "threshold": threshold  # <-- Return the dynamic threshold used
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)