import pandas as pd
import plotly.express as px

# Define the standard units for each telemetry channel
FEATURE_UNITS = {
    'Speed': 'km/h',
    'RPM': 'RPM',
    'Throttle': '%',
    'Brake': '(On/Off)',
    'nGear': 'Gear',
    'DRS': 'State'
}

def classify_event(top_features, raw_snapshot):
    """
    Applies physics-based heuristics to classify the anomaly type.

    Args:
        top_features: List of (feature_name, error_value) tuples.
        raw_snapshot: Dictionary of raw sensor values at the anomaly timestamp.
    """
    feature_names = {f[0] for f in top_features}

    # 1. SENSOR DROPOUT (CRITICAL)
    # Logic: Car is moving fast (Speed > 100), but a critical sensor reads 0.
    speed = raw_snapshot.get('Speed', 0)

    if speed > 100:
        # Check RPM
        if raw_snapshot.get('RPM', 1) == 0:
            return "SENSOR DROPOUT (RPM)", "System Critical"

        # [FIXED] Check Throttle (Was missing in previous version)
        # If Throttle is a top anomaly feature AND it reads 0 while moving fast
        if 'Throttle' in feature_names and raw_snapshot.get('Throttle', 0) == 0:
            return "SENSOR DROPOUT (THROTTLE)", "System Critical"

    # 2. LOCK-UP DETECTION
    # Logic: High Brake error + Speed error + Brake is active
    if 'Brake' in feature_names and 'Speed' in feature_names:
        if raw_snapshot.get('Brake', 0) > 50: # Hard braking
            return "DRIVER LOCK-UP", "Physical Event"

    # 3. TRACTION LOSS / WHEEL SPIN
    # Logic: High RPM error + High Throttle error + Speed error
    if 'RPM' in feature_names and 'Throttle' in feature_names:
        return "TRACTION LOSS", "Physical Event"

    # 4. DRS FAULT
    if 'DRS' in feature_names:
        return "DRS ACTUATION FAULT", "System Warning"

    return "ANOMALOUS BEHAVIOR", "Unclassified"


def generate_anomaly_explanation_text(anomaly_data: dict) -> str:
    """
    Generates a structured forensic report with classification.
    """
    if not anomaly_data or not anomaly_data.get("top_features"):
        return "Insufficient data for forensic analysis."

    seq_idx = anomaly_data['sequence_index']
    rec_err = anomaly_data['reconstruction_error']
    threshold = anomaly_data['threshold']
    top_features = anomaly_data['top_features']
    raw_snapshot = anomaly_data.get('raw_snapshot', {})

    # --- Run Classification ---
    event_type, severity = classify_event(top_features, raw_snapshot)

    # --- Build Explanation ---
    explanation = f"**EVENT #{seq_idx} CLASSIFICATION: {event_type}**\n"
    explanation += f"**SEVERITY:** {severity} (Error: {rec_err:.4f} / Threshold: {threshold:.4f})\n\n"

    explanation += "**PRIMARY INDICATORS:**\n"
    for i, (feature, error) in enumerate(top_features):
        unit = FEATURE_UNITS.get(feature, '')
        raw_val = raw_snapshot.get(feature, 'N/A')
        explanation += f"{i + 1}. **{feature}** (Val: {raw_val} {unit}) - Deviation Score: {error:.4f}\n"

    explanation += "\n**AI INTERPRETATION:**\n"

    # Contextual Summary
    if "SENSOR DROPOUT" in event_type:
        explanation += "CRITICAL FAILURE: Sensor reporting zero output while vehicle is at speed. Indicates wire harness failure, ECU disconnect, or signal jamming attack."
    elif event_type == "DRIVER LOCK-UP":
        explanation += "Detected sharp deceleration curve inconsistent with normal braking profile. Likely front-tire lockup or threshold braking overshoot."
    elif event_type == "TRACTION LOSS":
        explanation += "Detected RPM spike without corresponding speed increase. Indicates rear wheel spin or gearbox/clutch slip event."
    elif event_type == "DRS ACTUATION FAULT":
        explanation += "DRS state change detected outside authorized activation zones. Potential sensor failure or unauthorized driver input."
    else:
        explanation += f"Uncharacteristic variance detected in {top_features[0][0]} telemetry channel relative to baseline lap model."

    return explanation


def create_top_features_chart(anomaly_data: dict, title: str):
    """Creates a Plotly bar chart for the top contributing features."""
    top_features = anomaly_data.get("top_features", [])
    if not top_features: return None

    features_with_units = [f"{feat}" for feat, err in top_features]
    errors = [err for feat, err in top_features]

    top_df = pd.DataFrame({"feature": features_with_units, "error": errors})

    fig = px.bar(top_df, x="feature", y="error", title=title)
    fig.update_layout(xaxis_title=None, yaxis_title="Contribution Score")
    return fig