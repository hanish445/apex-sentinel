# Apex Sentinel v2.0.0

**Real-Time F1 Telemetry Integrity & Anomaly Detection System**

## 1. Project Overview

**Apex Sentinel** is a professional-grade, real-time AI anomaly detection system designed to analyze telemetry data from Formula 1 cars. It learns the complex patterns of normal vehicle behavior using an **LSTM Autoencoder** and flags deviant events with millisecond precision.

**Version 2.0.0** introduces a significant leap in forensic capability. Beyond simple anomaly detection, the system now **classifies** events (e.g., distinguishing between a driver lock-up and a sensor failure) and maps them physically onto a **live 2D track map**, providing engineers with immediate, context-aware intelligence.

## 2. Developer Acknowledgment
This project was developed with the assistance of advanced Generative AI tools, like **Gemini** and **ChatGPT**. These tools were utilized to assist with complex mathematical calculations for the physics-based heuristics, optimize the React rendering loops, and polish the dashboard UI for a professional "race-day" aesthetic.

## 3. Tech Stack

### Backend (The Brain)
* **Framework**: FastAPI (Python)
* **ML Engine**: TensorFlow / Keras (LSTM Autoencoder)
* **Data Source**: FastF1 (Official F1 Timing & Telemetry)
* **Data Processing**: Pandas, NumPy, Scikit-learn

### Frontend (The Monitor)
* **Framework**: React.js (v18+)
* **Build Tool**: Vite
* **Visualization**: Plotly.js (Real-time charts & Track Map)
* **Styling**: CSS Modules (Carbon/Neon F1 aesthetic)

## 4. Key Features (v2.0.0)

### 🧠 Advanced AI & Forensics (New in v2.0)
* **Automated Event Classification**: The system uses physics-based heuristics to classify anomalies into specific categories:
    * **Driver Lock-up**: Detected via brake pressure vs. deceleration deltas.
    * **Traction Loss**: Detected via RPM spikes inconsistent with speed (wheel spin).
    * **Sensor Failure**: Flags critical data dropouts (e.g., Speed > 100kph but RPM = 0).
    * **DRS Faults**: Identifies unauthorized DRS activation outside designated zones.
* **AI Interpretation**: Generates human-readable forensic reports explaining *why* an event was flagged (e.g., *"Detected sharp deceleration curve inconsistent with normal braking profile"*).

### 📍 Spatial Intelligence (New in v2.0)
* **Live 2D Track Map**: Renders the circuit geometry using GPS data.
* **Pinpoint Localization**: Plots the driver's live position (Yellow Marker) and exactly where anomalies occurred (Red 'X' Markers) on the track.

### 🏎️ Core Capabilities
* **LSTM Autoencoder**: Learns non-linear correlations between Speed, RPM, Throttle, Brake, Gear, and DRS.
* **Dynamic Thresholding**: Automatically calculates deviation limits based on training reconstruction error (Mean + 3 StdDev).
* **Real-Time Simulation**: Client-side loop plays back race data at 60Hz.
* **Live Telemetry Gauges**: Analog-style visualization for critical car metrics.

## 5. The Blend of AI/ML and Cyber Security
Apex Sentinel reframes a classic cybersecurity concept—the Intrusion Detection System (IDS)—for the physical world of high-performance engineering.

**Integrity Monitoring**: Just as an IDS flags malformed network packets, Apex Sentinel flags "malformed" physical data. A sensor sending static noise or a mechanical part failing mimics the signature of a cyber-attack on the vehicle's integrity.

**Context-Aware Defense**: Traditional rule-based systems ("Alert if RPM > 13k") create false positives. Apex Sentinel uses Deep Learning to understand context (e.g., High RPM is valid if Throttle is 100%, but invalid if Throttle is 0%). This is analogous to User and Entity Behavior Analytics (UEBA) in cyber defense.

**Availability Assurance**: By detecting the early onset of mechanical stress (e.g., micro-vibrations or traction anomalies), the system acts as a safeguard for the vehicle's availability, preventing catastrophic failure before it occurs.

## 6. How to Start Apex Sentinel

You will need two terminal windows running simultaneously (one for the Backend, one for the Frontend).

### Step 1: Backend Setup (Terminal 1)

1.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Prepare the Data & Model**:
    * Download telemetry (Default: 2023 Bahrain GP, PER):
        ```bash
        python src/data_collection.py
        ```
    * Preprocess and scale the data:
        ```bash
        python src/explore_data.py
        ```
    * Train the LTSM model:
        ```bash
        python src/train_model.py
        ```

3.  **Start the API Server**:
    ```bash
    python src/main.py
    ```
    *The API will start at `http://0.0.0.0:8000`*

### Step 2: Frontend Setup (Terminal 2)

1.  **Navigate to the dashboard directory**:
    ```bash
    cd apex-dashboard
    ```

2.  **Install Node modules**:
    ```bash
    npm install
    ```

3.  **Start the React Dashboard**:
    ```bash
    npm run dev
    ```

4.  **Open the App**:
    Visit the URL shown in the terminal (usually `http://localhost:5173`).

**Usage Workflow**:
1.  Click **LOAD DATA** to fetch the processed race data from the backend.
2.  Click **PLAY** to start the real-time simulation.
3.  Observe the **Live GPS** map and telemetry charts.
4.  Click **RUN DIAGNOSTICS** to perform a batch forensic scan of the entire session and view the **Anomaly Report** panel.
