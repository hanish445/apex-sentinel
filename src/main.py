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
from typing import List, Optional, Dict, Any

from data_collection import collect_telemetry_data
from anomaly_analysis import generate_anomaly_explanation_text, classify_event
from security_ledger import log_to_ledger

# --- Configuration ---
MODEL_PATH = os.path.join('models', 'anomaly_detector.keras')
SCALER_PATH = os.path.join('models', 'scaler.pkl')
THRESHOLD_PATH = os.path.join('models', 'threshold.json')
TIMESTEPS = 10
MODEL_FEATURES = ['Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS']

app = FastAPI(title="F1 Anomaly Detection API v2.5", version="2.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    model = tf.keras.models.load_model(MODEL_PATH)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    with open(THRESHOLD_PATH, 'r') as f:
        threshold_data = json.load(f)
        threshold = float(threshold_data['threshold'])
except Exception as e:
    model, scaler, threshold = None, None, None

class TelemetryData(BaseModel):
    Speed: List[float]
    RPM: List[float]
    Throttle: List[float]
    Brake: List[float]
    nGear: List[float]
    DRS: List[float]
    X: Optional[List[float]] = None
    Y: Optional[List[float]] = None
    Z: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = {}

class DataRequest(BaseModel):
    year: int
    gp: str
    session: str
    driver: str

@app.post("/load_data")
def load_race_data(req: DataRequest):
    try:
        # Get dataframe AND sector info
        df, error, sectors = collect_telemetry_data(req.year, req.gp, req.session, req.driver)
        if error: raise HTTPException(status_code=400, detail=error)

        if 'Brake' in df.columns and df['Brake'].dtype == 'bool':
            df['Brake'] = df['Brake'].astype(int)
        df = df.fillna(0)

        return {
            "telemetry": df.to_dict(orient="records"),
            "sectors": sectors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
def predict_anomaly(data: TelemetryData):
    if not all([model, scaler, threshold]):
        return {"error": "Model not loaded"}

    input_dict = data.dict()

    # [CRITICAL FIX] Remove metadata before Pandas conversion
    meta_data = {}
    if 'metadata' in input_dict:
        meta_data = input_dict['metadata']
        del input_dict['metadata']

    input_df = pd.DataFrame(input_dict)

    if not all(col in input_df.columns for col in MODEL_FEATURES):
        return {"error": f"Missing required columns: {MODEL_FEATURES}"}

    model_df = input_df[MODEL_FEATURES]

    if len(model_df) < TIMESTEPS:
        return {"is_anomaly": []}

    try:
        scaled_data = scaler.transform(model_df)
        sequences = np.array([scaled_data[i:i + TIMESTEPS] for i in range(len(scaled_data) - TIMESTEPS + 1)], dtype=np.float32)

        if sequences.size == 0: return {"is_anomaly": []}

        reconstructed = model.predict(sequences, verbose=0)
        reconstruction_error = np.mean(np.abs(sequences - reconstructed), axis=(1, 2))
        per_feature_error = np.mean(np.abs(sequences - reconstructed), axis=1)
        anomalies = reconstruction_error > threshold

    except Exception as e:
        return {"error": f"Inference failed: {str(e)}"}

    sequence_end_indices = [i + TIMESTEPS - 1 for i in range(len(sequences))]
    top_features_list = []
    explanations_list = []
    classifications_list = []
    forensic_receipts = []

    for i, seq_err in enumerate(per_feature_error):
        feat_map = {MODEL_FEATURES[j]: float(seq_err[j]) for j in range(len(MODEL_FEATURES))}
        sorted_feats = sorted(feat_map.items(), key=lambda kv: kv[1], reverse=True)
        top_3 = sorted_feats[:3]
        top_features_list.append(top_3)

        explanation = ""
        tag = "NORMAL"
        receipt = None

        if anomalies[i]:
            end_idx = sequence_end_indices[i]
            raw_snapshot = model_df.iloc[end_idx].to_dict()

            event_type, severity = classify_event(top_3, raw_snapshot)
            tag = event_type

            report = {
                "sequence_index": int(i),
                "end_index": int(end_idx),
                "threshold": float(threshold),
                "reconstruction_error": float(reconstruction_error[i]),
                "top_features": top_3,
                "raw_snapshot": raw_snapshot,
                "classification": event_type,
                "severity": severity
            }

            # --- LEDGER COMMIT ---
            event_id, event_hash, pdf_filename = log_to_ledger(report, meta_data)

            explanation = generate_anomaly_explanation_text(report)
            explanation += f"\n\n🔒 **CHAIN OF CUSTODY SECURED**\n"
            explanation += f"ID: {event_id}\n"
            explanation += f"HASH: {event_hash[:16]}...\n"
            explanation += f"EVIDENCE: {pdf_filename} generated."

            receipt = {"id": event_id, "hash": event_hash, "pdf": pdf_filename}

        explanations_list.append(explanation)
        classifications_list.append(tag)
        forensic_receipts.append(receipt)

    return {
        "is_anomaly": anomalies.tolist(),
        "reconstruction_error": reconstruction_error.tolist(),
        "threshold": float(threshold),
        "sequence_end_indices": sequence_end_indices,
        "top_features": top_features_list,
        "explanations": explanations_list,
        "classifications": classifications_list,
        "secure_receipts": forensic_receipts
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)