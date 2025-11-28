# Apex Sentinel v1.5.0

Real-Time F1 Telemetry Integrity & Anomaly Detection System

## Development Acknowledgment
This project was developed with the assistance of advanced Generative AI tools. AI was utilized to accelerate the architectural migration from Streamlit to React, optimize the data simulation loops, and refine the forensic reporting logic, demonstrating the effective collaboration between human engineering and artificial intelligence.

## 1. Project Overview

Description: Apex Sentinel is a professional-grade, real-time AI anomaly detection system designed to analyze telemetry data from Formula 1 cars. It learns the complex patterns of normal vehicle behavior using an LSTM Autoencoder and flags deviant events with millisecond precision, providing engineers with automated, context-aware forensic reports.

Goal: The primary goal is to proactively identify potential system failures, sensor glitches, or unexpected driver actions by monitoring the vehicle's data stream as an Intrusion Detection System (IDS) for physical assets.

## 2. The Blend of AI/ML and Cybersecurity

At its core, Apex Sentinel reframes a classic cybersecurity concept in the context of high-performance engineering.

### The Cybersecurity Parallel

In network security, an Intrusion Detection System (IDS) monitors network traffic for packets that deviate from a "normal" baseline. Apex Sentinel does the exact same thing, but instead of network packets, it monitors a stream of sensor data from the F1 car. An "intrusion" or "anomaly" in this context represents:

Integrity Loss: A compromised sensor sending faulty data.

Availability Risk: The beginning of a mechanical or electronic system failure.

Unknown State: An unexpected physical event (like a spin or impact) that puts the system outside its safety envelope.

### The AI/ML Advantage

Traditional rule-based systems (e.g., "Alert if RPM > 13,000") fail to capture context. Apex Sentinel uses Deep Learning to understand non-linear relationships. For example, it knows that high RPM is normal when throttle is 100%, but it correctly flags high RPM with 0% throttle as a critical anomaly. This contextual awareness allows it to detect subtle issues that static rules would miss.

## 3. Key Features (v1.5.0)

Version 1.5.0 introduces a major architectural overhaul, moving to a decoupled Client-Server model for enterprise-grade performance.

### Core Intelligence

LSTM Autoencoder: A sophisticated Deep Learning model built with TensorFlow that learns the intricate correlations between Speed, RPM, Throttle, Brake, Gear, and DRS.

Dynamic Thresholding: Automatically calculates statistical deviation limits based on training data reconstruction error (Mean + 3 StdDev).

### Professional Dashboard

React + Vite Engine: A completely rewritten frontend using React.js and Vite, delivering 60FPS performance and eliminating the UI jitter found in previous versions.

Client-Side Simulation: The telemetry loop now runs natively in the browser's JavaScript engine, ensuring smooth, non-blocking data playback.

Live Telemetry Gauges: Real-time analog-style visualization for Speed, RPM, and Throttle.

### Advanced Forensics Engine

Automated Root Cause Analysis: The system doesn't just flag errors; it explains them.

Context-Aware Reporting: Python logic analyzes the feature contribution vectors to generate human-readable explanations (e.g., distinguishing between a "Lock-up" and a "Power Unit" issue).

Batch Analysis: One-click forensic scan of the entire session to generate a detailed log of all anomaly events.

### F1 Data Engine

On-Demand Ingestion: Connects directly to the fastf1 library to download real-world telemetry from any recent F1 season (2018-2024), driver, or session type (FP1, Quali, Race).

## 4. Tech Stack

### Backend (The Brain)
Framework: FastAPI (Python),
ML Engine: TensorFlow / Keras,
Data Processing: Pandas, NumPy, Scikit-learn,
Source: FastF1 API

### Frontend (The Monitor)
Framework: React.js (v18+),
Build Tool: Vite,
Visualization: Plotly.js,
Styling: Custom CSS Modules

## 5. Installation & Usage

Running Apex Sentinel requires two active terminals: one for the API server and one for the Dashboard.

Prerequisites

Python 3.8+

Node.js & npm

## Step 1: Backend Setup (Terminal 1)

### 1. Install Python dependencies
```
pip install -r requirements.txt
```

### 2. Train the Model (First run only)
```
python src/data_collection.py  # Download sample data
python src/explore_data.py     # Preprocess & Scale
python src/train_model.py      # Train LSTM & Save Model
```

### 3. Start the API Server
```
uvicorn main:app --reload
http://127.0.0.1:8000
```

## Step 2: Frontend Setup (Terminal 2)

### 1. Navigate to dashboard directory
```
cd apex-dashboard
```

### 2. Install Node modules
```
npm install
```

### 3. Start the React Application
```
npm run dev
```

## 6. Workflow

Configure: Use the sidebar to select Year, GP, Session (Race, Quali, etc.), and Driver.

Load: Click "Load Data" to fetch telemetry from the Python backend.

Simulate: Click "Start Simulation" to begin the real-time playback. Watch the gauges and live charts for instantaneous anomaly markers.

Forensics: Click "Run Batch Analysis" to process the full lap. A "Forensics Report" panel will appear below, listing every detected event with a generated text explanation and root-cause bar chart.

## 7. Coming Soon for v2.0.0

The roadmap for the next major version of Apex Sentinel focuses on adding deeper layers of intelligence and context.

Intelligent Anomaly Classification: Training a second machine learning model (e.g., XGBoost) to automatically classify detected anomalies into meaningful categories, such as True Anomaly (likely a system failure) vs. False Positive (likely a driver-induced event like a spin or crash).

2D Track Map Visualization: Adding a new visualization panel to plot the physical X and Y location of each anomaly directly onto a 2D map of the circuit, providing crucial spatial context to every event.
