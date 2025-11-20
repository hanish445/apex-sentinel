import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
import tensorflow as tf
import pickle
import os

# --- Configuration ---
MODEL_PATH = os.path.join('models', 'anomaly_detector.keras')
SCALER_PATH = os.path.join('models', 'scaler.pkl')
TIMESTEPS = 10  # Must be the same as used in training

# --- FastAPI App Initialization ---
app = FastAPI(
    title="F1 Anomaly Detection API",
    description="API for detecting anomalies in F1 telemetry data using an LSTM autoencoder.",
    version="1.0.0"
)

# --- Load Model and Scaler at Startup ---
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    print("Model and scaler loaded successfully.")
except Exception as e:
    print(f"Error loading model or scaler: {e}")
    model = None
    scaler = None


# --- Define Request Body Structure ---
# This tells FastAPI what kind of data to expect in a POST request.
class TelemetryData(BaseModel):
    Speed: list[float]
    RPM: list[float]
    Throttle: list[float]
    Brake: list[float]
    nGear: list[float]
    DRS: list[float]


# --- API Endpoints ---
@app.get("/", tags=["Health Check"])
def read_root():
    """A simple endpoint to check if the API is running."""
    return {"status": "API is running"}


@app.post("/predict", tags=["Anomaly Detection"])
def predict_anomaly(data: TelemetryData):
    """
    Receives telemetry data, preprocesses it, and predicts anomalies.
    """
    if not model or not scaler:
        return {"error": "Model or scaler not loaded. Check server logs."}

    # Convert incoming data to a pandas DataFrame
    input_df = pd.DataFrame(data.dict())

    # Ensure we have enough data for at least one sequence
    if len(input_df) < TIMESTEPS:
        return {"error": f"Not enough data provided. Need at least {TIMESTEPS} timesteps."}

    # Preprocess the data using the loaded scaler
    scaled_data = scaler.transform(input_df)

    # Create sequences from the scaled data
    sequences = []
    for i in range(len(scaled_data) - TIMESTEPS + 1):
        sequences.append(scaled_data[i:i + TIMESTEPS])
    sequences = np.array(sequences)

    if len(sequences) == 0:
        return {"error": "Could not create any sequences from the provided data."}

    # Get the model's reconstruction of the sequences
    reconstructed_sequences = model.predict(sequences)

    # Calculate reconstruction error (Mean Absolute Error)
    reconstruction_error = np.mean(np.abs(sequences - reconstructed_sequences), axis=(1, 2))

    # Define an anomaly threshold (this may need tuning)
    # A common starting point is the mean + X standard deviations of the training reconstruction error
    # For now, we'll use a pre-defined heuristic value.
    threshold = 0.1

    # Determine which sequences are anomalous
    anomalies = reconstruction_error > threshold

    # Return the results
    return {
        "reconstruction_error": reconstruction_error.tolist(),
        "is_anomaly": anomalies.tolist(),
        "threshold": threshold
    }


# --- Run the API ---
if __name__ == "__main__":
    # This allows you to run the API directly for testing
    uvicorn.run(app, host="0.0.0.0", port=8000)