import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import os
import time
from datetime import datetime

from data_collection import collect_telemetry_data

# Configuration
API_URL = "http://127.0.0.1:8000/predict"
TIMESTEPS = 10  # must match model
DEFAULT_PLAYBACK_DELAY = 0.2  # seconds between steps

st.set_page_config(layout="wide")
st.title("Apex Sentinel")

st.write("Select session and driver, download the lap, then use 'Simulate Live Feed' to stream telemetry through the model.")

# UI: Data selection
SESSION_OPTIONS = {
    'Race': 'R', 'Qualifying': 'Q', 'Sprint': 'S',
    'FP1': 'FP1', 'FP2': 'FP2', 'FP3': 'FP3'
}

col1, col2, col3, col4 = st.columns(4)
with col1:
    year = st.number_input("Year", min_value=2018, max_value=datetime.now().year, value=2023)
with col2:
    grand_prix = st.text_input("Grand Prix Name", value="Bahrain")
with col3:
    session_key = st.selectbox("Session Type", options=list(SESSION_OPTIONS.keys()), index=0)
    session_type = SESSION_OPTIONS[session_key]
with col4:
    driver = st.text_input("Driver Abbreviation", value="PER", help="e.g., VER, PER, HAM, LEC")

# Playback controls
st.sidebar.header("Simulation Controls")
playback_delay = st.sidebar.slider("Playback delay (s)", min_value=0.05, max_value=2.0, value=DEFAULT_PLAYBACK_DELAY, step=0.05)
auto_start = st.sidebar.checkbox("Auto start after download", value=False)

# Placeholders
download_col = st.empty()
status_col = st.empty()
plots_col = st.empty()
controls_col = st.empty()

# Variables stored in session_state across reruns
if "telemetry_df" not in st.session_state:
    st.session_state.telemetry_df = None
if "anomaly_indices" not in st.session_state:
    st.session_state.anomaly_indices = []
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "current_step" not in st.session_state:
    st.session_state.current_step = TIMESTEPS - 1

def download_and_prepare():
    with st.spinner(f"Downloading data for {driver} at the {year} {grand_prix} GP..."):
        df, error_message = collect_telemetry_data(year, grand_prix, session_type, driver)
    if error_message:
        status_col.error(error_message)
        return False
    # Keep raw telemetry in session_state
    st.session_state.telemetry_df = df.reset_index(drop=True)
    # Ensure expected columns exist
    features = ['Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS']
    missing = [f for f in features if f not in st.session_state.telemetry_df.columns]
    if missing:
        status_col.error(f"Telemetry missing expected columns: {missing}")
        st.session_state.telemetry_df = None
        return False
    # Normalize Brake boolean to int if needed
    if st.session_state.telemetry_df['Brake'].dtype == 'bool':
        st.session_state.telemetry_df['Brake'] = st.session_state.telemetry_df['Brake'].astype(int)
    st.session_state.anomaly_indices = []
    st.session_state.current_step = TIMESTEPS - 1
    status_col.success("Telemetry downloaded and ready.")
    return True

def send_window_and_check_anomaly(window_df):
    """
    Sends a window_df (DataFrame with TIMESTEPS rows) to the API and returns boolean is_anomaly, reconstruction_error, threshold.
    """
    try:
        payload = window_df.to_dict(orient='list')
        resp = requests.post(API_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        is_anomaly_list = data.get("is_anomaly", [])
        # For a single sequence request, take first entry
        if isinstance(is_anomaly_list, list) and len(is_anomaly_list) >= 1:
            return bool(is_anomaly_list[0]), data.get("reconstruction_error", [None])[0], data.get("threshold")
        return False, None, data.get("threshold")
    except Exception as e:
        status_col.error(f"API request failed: {e}")
        return False, None, None

def build_plots(upto_index):
    """
    Build two Plotly figures: RPM only, and other channels.
    Mark anomalies from session_state.anomaly_indices (they correspond to indices in the original df).
    """
    df = st.session_state.telemetry_df
    features_other = ['Speed', 'Throttle', 'Brake', 'nGear', 'DRS']
    # RPM plot
    rpm_fig = go.Figure()
    rpm_fig.add_trace(go.Scatter(x=df.index[:upto_index+1], y=df['RPM'][:upto_index+1], mode='lines', name='RPM'))
    anomaly_points = [i for i in st.session_state.anomaly_indices if i <= upto_index]
    if anomaly_points:
        rpm_fig.add_trace(go.Scatter(x=anomaly_points, y=df.loc[anomaly_points, 'RPM'], mode='markers', marker=dict(color='red', size=8, symbol='x'), name='Anomaly'))
    rpm_fig.update_layout(title="RPM", xaxis_title="Time Step", yaxis_title="RPM", height=300)

    # Other telemetry plot
    other_fig = go.Figure()
    for feat in features_other:
        other_fig.add_trace(go.Scatter(x=df.index[:upto_index+1], y=df[feat][:upto_index+1], mode='lines', name=feat))
    if anomaly_points:
        # For each feature, overlay anomaly markers
        for feat in features_other:
            other_fig.add_trace(go.Scatter(x=anomaly_points, y=df.loc[anomaly_points, feat], mode='markers', marker=dict(color='red', size=8, symbol='x'), name=f'{feat} Anom', showlegend=False))
    other_fig.update_layout(title="Other Telemetry (Speed, Throttle, Brake, nGear, DRS)", xaxis_title="Time Step", height=350)

    return rpm_fig, other_fig

# Buttons
col_a, col_b, col_c = download_col.columns(3)
with col_a:
    if st.button("Download Lap Data"):
        ok = download_and_prepare()
        if ok and auto_start:
            st.session_state.is_running = True
with col_b:
    if st.button("Start Simulation"):
        if st.session_state.telemetry_df is None:
            status_col.error("No telemetry loaded. Download first.")
        else:
            st.session_state.is_running = True
with col_c:
    if st.button("Stop / Reset"):
        st.session_state.is_running = False
        st.session_state.telemetry_df = None
        st.session_state.anomaly_indices = []
        st.session_state.current_step = TIMESTEPS - 1
        status_col.info("Stopped and reset.")

# Main simulation loop (runs while is_running)
if st.session_state.telemetry_df is not None:
    total_len = len(st.session_state.telemetry_df)
    plots_placeholder = plots_col.empty()
    controls_placeholder = controls_col.empty()

    # Show static info
    with controls_placeholder.container():
        st.write(f"Telemetry length: {total_len} rows")
        st.write(f"Current index: {st.session_state.current_step}/{total_len-1}")
        st.write(f"Detected anomalies so far: {len(st.session_state.anomaly_indices)}")

    # Draw initial plots
    rpm_fig, other_fig = build_plots(st.session_state.current_step)
    with plots_placeholder.container():
        st.plotly_chart(rpm_fig, use_container_width=True)
        st.plotly_chart(other_fig, use_container_width=True)

    # If simulation running, iterate
    if st.session_state.is_running:
        # Iterate steps from current_step+1 to end
        for idx in range(st.session_state.current_step + 1, total_len):
            # Ensure we can stop quickly
            if not st.session_state.is_running:
                break

            # Prepare the latest TIMESTEPS window
            if idx - TIMESTEPS + 1 < 0:
                continue
            window_df = st.session_state.telemetry_df.iloc[idx - TIMESTEPS + 1: idx + 1][['Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS']]

            is_anom, rec_err, threshold = send_window_and_check_anomaly(window_df)
            if is_anom:
                st.session_state.anomaly_indices.append(idx)

            st.session_state.current_step = idx

            # Update status
            status_col.info(f"Step {idx}/{total_len-1} — Anomaly: {is_anom} — RecErr: {rec_err} — Thresh: {threshold}")

            # Rebuild plots and display
            rpm_fig, other_fig = build_plots(idx)
            with plots_placeholder.container():
                st.plotly_chart(rpm_fig, use_container_width=True)
                st.plotly_chart(other_fig, use_container_width=True)
                st.markdown(f"**Anomalies detected:** {len(st.session_state.anomaly_indices)}")

            # Wait according to playback speed
            time.sleep(playback_delay)

        st.session_state.is_running = False
        status_col.success("Simulation finished.")
else:
    status_col.info("Download a lap to begin simulation.")