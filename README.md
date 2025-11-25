# 🏁 Apex Sentinel V 1.0.0

### 1. Project Overview

**Name:** Apex Sentinel

**Description:** Apex Sentinel is a real-time, AI-powered anomaly detection system designed to analyze telemetry data from Formula 1 cars. It learns the complex patterns of normal vehicle behavior and flags any deviations, providing engineers and strategists with detailed, automated explanations for each detected event.

**Goal:** The primary goal of Apex Sentinel is to proactively identify potential system failures, unexpected driver actions, or other unusual events by monitoring a vehicle's data stream in real-time. By catching these anomalies early, the system aims to enhance reliability, performance, and strategic decision-making.

---

### 2. Key Features

Apex Sentinel V 1.0.0 is a complete, end-to-end application with a rich feature set:

*   **🧠 Core AI Anomaly Detection:** Utilizes a sophisticated LSTM (Long Short-Term Memory) Autoencoder built with TensorFlow to learn the intricate relationships between different telemetry channels.
*   **📈 Dynamic Anomaly Threshold:** Automatically calculates a statistical threshold after training, ensuring that anomaly detection is robust and data-driven, not based on arbitrary fixed values.
*   **☁️ On-Demand F1 Data Engine:** Connects directly to the `fastf1` library to download real-world telemetry from any recent F1 season, allowing for analysis of specific drivers, sessions, and Grand Prix.
*   **⚙️ Robust API Backend:** A high-performance backend built with FastAPI that serves the trained model and provides a detailed JSON response for prediction and explainability requests.
*   **🖥️ Interactive Simulation Dashboard:** A user-friendly web interface built with Streamlit that allows for:
    *   Dynamic selection of race data.
    *   Real-time simulation of a lap, with live-updating telemetry plots.
    *   Immediate visual marking of detected anomalies on graphs.
*   **🤖 Advanced Explainability Engine:** The standout feature of Apex Sentinel. It doesn't just find anomalies; it explains them:
    *   **Automated Text Summaries:** Generates human-readable reports for each anomaly.
    *   **Dynamic Interpretation:** The explanation text is context-aware, changing based on which telemetry channels caused the anomaly (e.g., an `RPM` and `Throttle` issue gets a different explanation than a `Brake` and `Speed` issue).
    *   **Root Cause Charting:** Automatically generates a bar chart showing the top 3 contributing features for any anomaly.
*   **📑 Batch Analysis & Reporting:** After a simulation, a full "batch analysis" can be run to generate a comprehensive log of all anomalies from the lap, with options to inspect each one and download a JSON report.

---

### 3. The Blend of AI/ML and Cybersecurity

At its core, Apex Sentinel is an **Intrusion Detection System (IDS) for a physical asset**. It reframes a classic cybersecurity concept in the context of high-performance engineering.

*   **The Cybersecurity Parallel:** In network security, an IDS monitors network traffic for patterns that deviate from a "normal" baseline, flagging potential intrusions. Apex Sentinel does the exact same thing, but instead of network packets, it monitors a stream of sensor data from a physical system—the F1 car. An "intrusion" or "anomaly" could represent:
    *   A compromised sensor sending faulty data.
    *   The beginning of a mechanical or electronic system failure.
    *   An unexpected physical event (like a spin or impact) that puts the system in an unknown state.
    
    By monitoring this data integrity, we are working to protect the car's performance, reliability, and the safety of its systems.

*   **The AI/ML Advantage:** A traditional system might use simple rules (e.g., "alert if RPM > 12,000"). The AI/ML model in Apex Sentinel is far more powerful. It learns the **complex, non-linear relationships** between *all* telemetry channels. For example, it knows that high RPM is normal when the throttle is high and the gear is low, but it would correctly flag high RPM with zero throttle as a major anomaly. This ability to understand **context** across dozens of data points is what allows it to detect subtle issues that a rule-based system would miss.

---

### 4. How to Run the Software

To get Apex Sentinel running, follow these steps.

#### Prerequisites
*   Python 3.8+
*   `pip` for installing packages

#### Step 1: Clone the Repository
```bash
git clone <your-repository-url>
cd <your-repository-name>
```

#### Step 2: Install Dependencies
It's recommended to use a virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install all required packages
pip install -r requirements.txt
```
*(You will need to create a `requirements.txt` file containing `streamlit`, `fastapi`, `uvicorn`, `tensorflow`, `pandas`, `plotly`, `scikit-learn`, and `fastf1`)*

#### Step 3: Train the Anomaly Detection Model
Before you can run the application, you must train the AI model. This will create the necessary model and scaler files in the `models/` directory.
```bash
python train_model.py
```

#### Step 4: Run the API Backend
In your first terminal, start the FastAPI server. This will host your model.
```bash
uvicorn main:app --reload
(or)
python main.py
```
Leave this terminal running.

#### Step 5: Run the Streamlit Dashboard
In a **second** terminal, run the Streamlit web application.
```bash
streamlit run dashboard.py
```
Your web browser should automatically open with the Apex Sentinel dashboard.

#### Step 6: Use the Application
1.  Use the input fields on the main page to select a Year, Grand Prix, Session, and Driver.
2.  Click **"Download Lap Data"**.
3.  Once the data is ready, click **"Start Simulation"** to see the engine in action.
4.  After the simulation, click **"Run Explainability (Batch)"** to analyze the results.

---

### 5. Coming Soon for V 2.0.0

The roadmap for the next major version of Apex Sentinel focuses on adding deeper layers of intelligence and context.

*   **Intelligent Anomaly Classification:** Training a second machine learning model (e.g., XGBoost) to automatically classify detected anomalies into meaningful categories, such as `True Anomaly` (likely a system failure) vs. `False Positive` (likely a driver-induced event like a spin or crash).
*   **2D Track Map Visualization:** Adding a new visualization panel to plot the physical `X` and `Y` location of each anomaly directly onto a 2D map of the circuit, providing crucial spatial context to every event.
