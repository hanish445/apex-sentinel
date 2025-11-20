import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import os
from datetime import datetime

# Import the data collection function from our other script
from data_collection import collect_telemetry_data

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/predict"
TIMESTEPS = 10  # Must match the model's training


def plot_results(df, results, title):
    """Helper function to create a plot for a given set of features."""
    features_to_plot = df.columns
    fig = go.Figure()

    anomaly_indices = [i + TIMESTEPS - 1 for i, is_anomaly in enumerate(results.get("is_anomaly", [])) if is_anomaly]

    for feature in features_to_plot:
        # Normal data trace
        fig.add_trace(go.Scatter(x=df.index, y=df[feature], mode='lines', name=feature))
        # Anomaly markers
        fig.add_trace(go.Scatter(
            x=anomaly_indices, y=df.loc[anomaly_indices, feature],
            mode='markers', name=f'{feature} Anomaly',
            marker=dict(color='red', size=8, symbol='x'),
            showlegend=False
        ))

    fig.update_layout(title=title, xaxis_title="Time Step", yaxis_title="Value", height=400)
    st.plotly_chart(fig, use_container_width=True)


# --- UI Layout ---
st.set_page_config(layout="wide")
st.title("Apex Sentinel")
st.write("Select a session to analyze a driver's fastest lap against the baseline AI model.")

# --- User Input Section ---
st.header("1. Select Data for Analysis")

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

if st.button("Analyze Lap Data"):
    with st.spinner(f"Downloading data for {driver} at the {year} {grand_prix} GP..."):
        df, error_message = collect_telemetry_data(year, grand_prix, session_type, driver)

    if error_message:
        st.error(error_message)
    else:
        st.success(f"Successfully downloaded data for {driver}'s fastest lap.")
        st.header("2. Analysis Results")

        features = ['Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS']
        telemetry_to_send = df[features]
        if telemetry_to_send['Brake'].dtype == 'bool':
            telemetry_to_send['Brake'] = telemetry_to_send['Brake'].astype(int)

        with st.spinner("Sending data to the AI model for analysis..."):
            try:
                response = requests.post(API_URL, json=telemetry_to_send.to_dict(orient='list'))
                response.raise_for_status()
                results = response.json()
                st.success("Analysis complete!")

                # --- Visualization ---
                st.subheader("Telemetry Plots with Anomalies Highlighted")

                # Plot 1: RPM
                rpm_df = telemetry_to_send[['RPM']]
                plot_results(rpm_df, results, "RPM Analysis")

                # Plot 2: Other Telemetry
                other_df = telemetry_to_send.drop(columns=['RPM'])
                plot_results(other_df, results, "Other Telemetry Analysis (Speed, Throttle, etc.)")

                num_anomalies = sum(results.get("is_anomaly", []))
                st.metric(label="Total Anomalous Time Steps Detected", value=num_anomalies)

            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the API at {API_URL}. Is the backend running? \n\nError: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")