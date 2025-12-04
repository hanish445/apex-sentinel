# Apex Sentinel v2.5.0 (Final)

## Data Fidelity & Limitations

**Apex Sentinel** is built on public telemetry data provided by the [FastF1](https://docs.fastf1.dev/) library. Users should be aware of the following physical limitations:

* **Sample Rate:** Public F1 telemetry is sampled at ~4-10Hz. High-frequency vibration attacks or micro-second sensor glitches may be lost in downsampling.
* **GPS Precision:** Geospatial data has a variance of ±10m compared to military-grade RTK-GPS used by teams.
* **Telemetry Latency:** This system operates on "Near Real-Time" data (delayed by API ingestion), whereas a production version would require direct CAN bus access (milliseconds latency).

*Note: The AI models have been tuned to accommodate this noise floor using dynamic thresholding.*

## Developer Acknowledgment
Developed with the assistance of advanced AI tools (**Gemini / ChatGPT**) to accelerate complex mathematical modeling for sector analysis, optimize the React simulation loop for 60FPS, and refine the forensic reporting architecture. This project demonstrates the effective collaboration between human engineering and artificial intelligence.

---

### Description
**Apex Sentinel** is a security engine designed to protect high-performance physical assets. Unlike traditional firewalls that inspect data packets, Apex Sentinel inspects **"physical physics"**. That is to ensure the components obey the laws of **vehicle dynamics**

It uses a **Deep Learning LSTM (Long-Short Term Memory) Autoencoder** to learn the baseline behavior of a Formula 1 car and detects anomalies—whether caused by mechanical failure, sensor degradation, or malicious cyber-attacks—in real-time.

---

## Key Features (v2.5.0 Final)

### 1. Active Defense: The "Red Team" Module
A built-in adversarial testing suite to validate the AI's resilience.
* **Sensor Jamming:** Simulates a "frozen" sensor attack (e.g., RPM stuck at 0).
* **Signal Drift:** Injects gradual bias into throttle sensors to mimic calibration hacks.
* **GPS Spoofing:** Teleports the vehicle coordinates to test geospatial integrity.

### 2. Forensic Integrity: The "Black Box" Ledger
A cryptographically secure chain of custody for evidence.
* **Immutable Logging:** Every detected anomaly is hashed (SHA-256) and linked to the previous entry, creating a local blockchain.
* **Evidence Receipts:** Automatically generates professional **PDF Forensic Reports** for every incident, ready for audit or stewards.

### 3. Visual Intelligence: Broadcast-Grade Dashboard
* **Live Sector Analysis:** Tracks vehicle performance against Session Bests (Purple) and Personal Bests (Green).
* **Telemetry Heatmaps:** "Engineering Mode" visualizes speed and braking zones dynamically on the track map.
* **Real-Time Gauges:** Analog-style visualization for Speed, RPM, Throttle, Brake, and Gear.

---

## System Architecture

### Backend
* **Engine:** Python / FastAPI
* **AI Model:** TensorFlow Keras (LSTM Autoencoder)
* **Data Processing:** Pandas, NumPy, Scikit-learn
* **Source:** FastF1 API (Live Telemetry & GPS)

### Frontend
* **Framework:** React.js (v19) + Vite
* **Visualization:** Plotly.js (WebGL Maps & Charts)
* **Performance:** 60Hz Client-Side Simulation Loop

---

## Quick Start

### Prerequisites
* Python 3.10+
* Node.js 18+

### 1. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the data pipeline (Download 2023 Bahrain Data)
python src/data_collection.py

# Train the AI Model (Generates 'anomaly_detector.keras')
python src/explore_data.py
python src/train_model.py

# Start the API Server
uvicorn src.main:app --reload
```

### 2. Frontend Setup
```bash
cd apex-dashboard
npm install
npm run dev
```
Open http://localhost:5173 in the browser

## How to demonstrate the Security Engine
### Scenario 1: "Dead Sensor" 
* Load any Session and select a driver. Ex: **2023 Bahrain GP PER (Sergio Perez)**
* Wait for Car to come to a position of your choice. Ex: Turn 1
* Click **JAM RPM SENSOR** button in the sidebar (click once again to stop)
* Obeservation: RPM drop to 0 but Speed stay high
* After clicking on **RUN DIAGNOSTICS** click on **OPEN REPORT**
* You must see **SENSOR DROPOUT** as a flagged Anomaly in the report

### Scenario 2: "Evidence Tamper"
* Create a session analysis (with any attacks, race and driver of your choice)
* Open the **reports/evidence/** folder on your computer
* Open the generated PDF Receipt
**Verification**: Note the **SHA-256** Hash at the bottom. This hash matches the entry in reports/secure_ledger.json. Any modification to the log file breaks the chain
