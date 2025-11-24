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

def get_dynamic_interpretation(top_features: list) -> str:
    """
    Generates a dynamic interpretation based on the top contributing features of an anomaly.

    Args:
        top_features: A list of tuples, where each tuple is (feature_name, error_value).

    Returns:
        A specific, context-aware interpretation string.
    """
    if not top_features:
        return "Could not determine a specific interpretation without feature data."

    # Extract just the names of the top features for easier lookup
    feature_names = {feature for feature, error in top_features}

    interpretations = []

    # Rule-based interpretations
    if 'RPM' in feature_names and 'Throttle' in feature_names:
        interpretations.append(
            "High error in both **RPM and Throttle** often points to a power unit issue, an unexpected gear shift, or a loss of traction where engine speed is inconsistent with throttle input.")
    elif 'RPM' in feature_names:
        interpretations.append(
            "A significant deviation in **RPM** could suggest an engine irregularity, a missed gear shift, or hitting the rev limiter unexpectedly.")
    elif 'Throttle' in feature_names:
        interpretations.append(
            "An anomaly in **Throttle** might indicate erratic driver input or a problem with the throttle application sensor.")

    if 'Brake' in feature_names and 'Speed' in feature_names:
        interpretations.append(
            "When **Brake and Speed** are flagged together, it could signal a wheel lock-up under braking, a spin, or a driver action that deviates heavily from normal braking zones.")
    elif 'Brake' in feature_names:
        interpretations.append(
            "Unusual **Brake** data can indicate braking at an unexpected point on the track, a sensor glitch (flickering on/off), or a sign of brake-related issues like fading.")

    if 'DRS' in feature_names:
        interpretations.append(
            "A **DRS** anomaly is significant as it suggests the drag reduction system was activated or deactivated outside of a normal zone, potentially indicating a malfunction or a strategic error.")

    # If no specific rules were met, provide a general summary based on the top feature.
    if not interpretations and top_features:
        top_feature_name = top_features[0][0]
        interpretations.append(
            f"The primary deviation was in **{top_feature_name}**. This indicates that its behavior was the most uncharacteristic aspect of this event, warranting a closer look at its data trace.")

    # Combine all relevant interpretations
    final_interpretation = "\n- **Interpretation**: " + " ".join(interpretations)
    final_interpretation += "\n\n> **Recommendation**: Always review the raw telemetry graphs around this time step to correlate these findings with specific on-track events or potential system malfunctions."

    return final_interpretation


def generate_anomaly_explanation_text(anomaly_data: dict) -> str:
    """
    Generates a human-readable text summary for a single anomaly's explainability report, including units and dynamic interpretation.

    Args:
        anomaly_data: A dictionary containing details for one anomaly.

    Returns:
        A formatted string explaining the anomaly.
    """
    if not anomaly_data or not anomaly_data.get("top_features"):
        return "Not enough data to generate a detailed explanation for this anomaly."

    seq_idx = anomaly_data['sequence_index']
    end_idx = anomaly_data['end_index']
    rec_err = anomaly_data['reconstruction_error']
    threshold = anomaly_data['threshold']
    top_features = anomaly_data['top_features']

    # --- Build Explanation ---
    explanation = f"**Analysis of Anomaly in Sequence {seq_idx} (ending at time step {end_idx})**\n\n"
    explanation += f"- **Severity**: The model's reconstruction error was **{rec_err:.6f}**, which is significantly above the anomaly threshold of **{threshold:.6f}**. "
    explanation += "_(Note: Error and threshold are unitless statistical measures of deviation.)_\n"
    explanation += "- **Primary Cause**: The anomaly was primarily driven by unexpected deviations in the following telemetry channels:\n"

    for i, (feature, error) in enumerate(top_features):
        unit = FEATURE_UNITS.get(feature, 'unitless')
        explanation += f"    {i + 1}. **{feature}** (Unit: {unit}): This channel was the most significant contributor to the error. Its behavior was highly uncharacteristic.\n"

    # --- Add Dynamic Interpretation ---
    dynamic_interpretation = get_dynamic_interpretation(top_features)
    explanation += dynamic_interpretation

    return explanation


def create_top_features_chart(anomaly_data: dict, title: str):
    """
    Creates a Plotly bar chart for the top contributing features of an anomaly.
    """
    top_features = anomaly_data.get("top_features", [])
    if not top_features:
        return None

    features_with_units = [f"{feat} ({FEATURE_UNITS.get(feat, '')})" for feat, err in top_features]
    errors = [err for feat, err in top_features]

    top_df = pd.DataFrame({
        "feature": features_with_units,
        "error": errors
    })

    fig = px.bar(top_df, x="feature", y="error", title=title)
    fig.update_layout(xaxis_title="Telemetry Channel (Unit)", yaxis_title="Contribution to Anomaly (Unitless Error)")
    return fig