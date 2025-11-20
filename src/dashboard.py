import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import os
import matplotlib.pyplot as plt

from main import TIMESTEPS

API_URL = "http://127.0.0.1:8000/predict"
TELEMETRY_DATA_PATH = os.path.join('data', 'telemetry_data.csv')

def plot_telemetry_with_anomalies(df, is_anomaly_list, features_to_plot):
    fig = go.Figure()
    num_plots = len(features_to_plot)
    fig, axes = plt.subplots(num_plots, 1, figsize=(15, 2 * num_plots), sharex=True)
    if num_plots == 1:
        axes = [axes]

    anomaly_series = pd.Series(False, index=df.index)
    prediction_indices = df.index[TIMESTEPS - 1:len(is_anomaly_list) + TIMESTEPS - 1]
    anomaly_series.loc[prediction_indices[is_anomaly_list]] = True

    for i, feature in enumerate(features_to_plot):
        axes[i].plot(df.index, df[feature], label='Normal', color='cornflowerblue', zorder=1)

        animalous_data = df[anomaly_series]
        axes[i].scatter(animalous_data.index, animalous_data[feature], color='crimson', label='Anomaly', zorder=2, s=20)

        axes[i].set_ylabel(feature)
        if i == 0:
            axes[i].legend()

    axes[-1].set_xlabel('Time step')
    plt.tight_layout()
    st.pyplot(fig)

st.set_page_config(layout="wide")
st.title("Apex Sentinel")

st.write("""
This dashboard simulates real-time analysis of F1 car telemetry.
Click the button below to fetch the latest lap data and run it through our AI Model to detect anomalies
""")

if st.button("Analyse latest lap data"):
    if not os.path.exists(TELEMETRY_DATA_PATH):
        st.error(f"Data file not found at {TELEMETRY_DATA_PATH}. Please run `python src/data_collection.py` first.")
    else:
        df = pd.read_csv(TELEMETRY_DATA_PATH)

        features = ['Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS']
        telemetry_to_send = df[features]

        if telemetry_to_send['Brake'].dtype == 'bool':
            telemetry_to_send['Brake'] = telemetry_to_send['Brake'].astype(int)

        st.info("Sending data to the Anomaly Detection API...")

        try:
            # 2. Send data to the API
            response = requests.post(API_URL, json=telemetry_to_send.to_dict(orient='list'))
            response.raise_for_status()  # Raise an exception for bad status codes

            results = response.json()
            st.success("Analysis complete! Plotting results...")

            # 3. Display results
            st.subheader("Analysis Results")

            # Use Plotly for interactive charts
            fig = go.Figure()

            # The API returns anomaly flags for each sequence. We need to align this with the original data.
            # The prediction for a sequence corresponds to the end of that sequence.
            TIMESTEPS = 10  # This must match the model's setting
            anomaly_indices = [i + TIMESTEPS - 1 for i, is_anomaly in enumerate(results.get("is_anomaly", [])) if
                               is_anomaly]

            for feature in features:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df[feature],
                    mode='lines',
                    name=feature,
                    legendgroup=feature
                ))
                # Add anomaly markers
                fig.add_trace(go.Scatter(
                    x=anomaly_indices,
                    y=df.loc[anomaly_indices, feature],
                    mode='markers',
                    name=f'{feature} Anomaly',
                    marker=dict(color='red', size=8, symbol='x'),
                    legendgroup=feature,
                    showlegend=False
                ))

            fig.update_layout(
                title="Telemetry Data with Detected Anomalies",
                xaxis_title="Time Step",
                yaxis_title="Value",
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to the API at {API_URL}. Is the backend running? \n\nError: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")