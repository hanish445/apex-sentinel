import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import './App.css';

// --- CONFIG ---
const API_URL = "http://127.0.0.1:8000";
const TIMESTEPS = 10;

// [CRITICAL] Exact Session Mapping from Dashboard.py
const SESSION_OPTIONS = {
    'Race': 'R', 'Qualifying': 'Q', 'Sprint': 'S',
    'FP1': 'FP1', 'FP2': 'FP2', 'FP3': 'FP3'
};

function App() {
    // --- STATE ---
    const [config, setConfig] = useState({ year: 2023, gp: "Bahrain", sessionKey: "Race", driver: "PER" });
    const [fullData, setFullData] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(TIMESTEPS);
    const [isRunning, setIsRunning] = useState(false);
    const [loading, setLoading] = useState(false);
    const [metrics, setMetrics] = useState({ Speed: 0, RPM: 0, nGear: 0, Throttle: 0, Brake: 0 });

    // Forensics Data
    const [analysisResults, setAnalysisResults] = useState(null);
    const [selectedAnomalyIndex, setSelectedAnomalyIndex] = useState(null);

    // --- ACTIONS ---

    // 1. CLEAR DATA
    const handleClear = () => {
        setIsRunning(false);
        setFullData([]);
        setAnalysisResults(null);
        setSelectedAnomalyIndex(null);
        setCurrentIndex(TIMESTEPS);
        setMetrics({ Speed: 0, RPM: 0, nGear: 0, Throttle: 0, Brake: 0 });
    };

    // 2. LOAD DATA
    const handleLoadData = async () => {
        handleClear(); // Clear previous session first
        setLoading(true);
        try {
            // Convert sessionKey (e.g., 'Race') to 'R'
            const payload = {
                ...config,
                session: SESSION_OPTIONS[config.sessionKey]
            };

            const res = await axios.post(`${API_URL}/load_data`, payload);
            setFullData(res.data);
            setCurrentIndex(TIMESTEPS);
        } catch (err) {
            alert(`Error loading data: ${err.response?.data?.detail || err.message}`);
        } finally {
            setLoading(false);
        }
    };

    // 3. RUN ANALYSIS (Now fetches Python explanations)
    const handleRunAnalysis = async () => {
        if (!fullData.length) return;
        setLoading(true);
        try {
            const payload = {
                Speed: fullData.map(d => d.Speed),
                RPM: fullData.map(d => d.RPM),
                Throttle: fullData.map(d => d.Throttle),
                Brake: fullData.map(d => d.Brake),
                nGear: fullData.map(d => d.nGear),
                DRS: fullData.map(d => d.DRS)
            };

            const res = await axios.post(`${API_URL}/predict`, payload);
            setAnalysisResults(res.data);

            const firstAnom = res.data.is_anomaly.findIndex(x => x === true);
            if (firstAnom !== -1) setSelectedAnomalyIndex(firstAnom);

        } catch (err) {
            alert("Analysis failed.");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // --- SIMULATION LOOP ---
    useEffect(() => {
        let interval;
        if (isRunning && fullData.length > 0 && currentIndex < fullData.length) {
            interval = setInterval(() => {
                setCurrentIndex(prev => prev + 1);
                setMetrics(fullData[currentIndex]);
            }, 50);
        } else if (currentIndex >= fullData.length) {
            setIsRunning(false);
        }
        return () => clearInterval(interval);
    }, [isRunning, currentIndex, fullData]);

    // --- CHART HELPERS ---
    const getLayout = (title) => ({
        autosize: true,
        title: { text: title, font: { color: '#f4f4f5', size: 14, family: 'Inter' }, x: 0.05 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { t: 40, r: 20, l: 40, b: 30 },
        showlegend: true,
        legend: { orientation: 'h', y: 1.1, font: { color: '#a1a1aa' } },
        xaxis: { showgrid: false, color: '#3f3f46' },
        yaxis: { gridcolor: '#27272a', color: '#a1a1aa' },
        font: { family: 'Inter' }
    });

    return (
        <div className="app-container">

            {/* SIDEBAR */}
            <aside className="sidebar">
                <div className="brand">🏎️ <span>APEX</span> SENTINEL</div>

                <div className="control-section">
                    <label className="label-text">Configuration</label>
                    <input className="input-field" type="number" placeholder="Year" value={config.year} onChange={e => setConfig({...config, year: parseInt(e.target.value)})} />
                    <input className="input-field" placeholder="Grand Prix" value={config.gp} onChange={e => setConfig({...config, gp: e.target.value})} />

                    {/* [CRITICAL] Session Type Dropdown */}
                    <select
                        className="select-field"
                        value={config.sessionKey}
                        onChange={e => setConfig({...config, sessionKey: e.target.value})}
                    >
                        {Object.keys(SESSION_OPTIONS).map(opt => (
                            <option key={opt} value={opt}>{opt}</option>
                        ))}
                    </select>

                    <input className="input-field" placeholder="Driver (e.g. PER)" value={config.driver} onChange={e => setConfig({...config, driver: e.target.value})} />

                    <button className="btn btn-primary" onClick={handleLoadData} disabled={loading}>
                        {loading ? "Loading..." : "⬇ Load Data"}
                    </button>

                    {/* [CRITICAL] Clear Button */}
                    <button className="btn btn-outline" onClick={handleClear} disabled={loading}>
                        Clear Data
                    </button>
                </div>

                <div className="divider" style={{height: '1px', background: '#3f3f46', margin: '10px 0'}}></div>

                <div className="control-section">
                    <label className="label-text">Simulation</label>
                    <button className={`btn btn-outline ${isRunning ? 'active' : ''}`} onClick={() => setIsRunning(!isRunning)} disabled={!fullData.length}>
                        {isRunning ? "Pause" : "Start Simulation"}
                    </button>
                </div>

                <div className="control-section">
                    <label className="label-text">Forensics</label>
                    <button className="btn btn-outline" onClick={handleRunAnalysis} disabled={!fullData.length}>
                        Run Batch Analysis
                    </button>
                </div>

                <div className="status-badge">
                    <span className="label-text">System Status</span>
                    <div className={`status-indicator ${isRunning ? 'live' : ''}`} />
                </div>
            </aside>

            {/* MAIN VIEW */}
            <main className="main-view">

                <div className="metrics-grid">
                    <MetricCard label="Speed" value={Math.round(metrics.Speed)} unit="km/h" />
                    <MetricCard label="RPM" value={Math.round(metrics.RPM)} unit="" />
                    <MetricCard label="Gear" value={metrics.nGear} unit="" />
                    <MetricCard label="Throttle" value={Math.round(metrics.Throttle)} unit="%" />
                    <MetricCard label="Brake" value={metrics.Brake ? "ON" : "OFF"} unit="" />
                </div>

                <div className="viz-container">
                    <div className="chart-panel">
                        <Plot
                            data={[
                                { x: fullData.slice(0, currentIndex).map((_, i) => i), y: fullData.slice(0, currentIndex).map(d => d.Speed), type: 'scatter', mode: 'lines', name: 'Speed', line: {color: '#3b82f6', width: 2} },
                                { x: fullData.slice(0, currentIndex).map((_, i) => i), y: fullData.slice(0, currentIndex).map(d => d.Throttle), type: 'scatter', mode: 'lines', name: 'Throttle', line: {color: '#22c55e', width: 1}, yaxis: 'y2' }
                            ]}
                            layout={{
                                ...getLayout('Telemetry Trace'),
                                yaxis2: { overlaying: 'y', side: 'right', showgrid: false }
                            }}
                            style={{width: '100%', height: '100%'}}
                            useResizeHandler={true}
                        />
                    </div>
                    <div className="chart-panel">
                        <Plot
                            data={[
                                { x: fullData.slice(0, currentIndex).map((_, i) => i), y: fullData.slice(0, currentIndex).map(d => d.RPM), type: 'scatter', mode: 'lines', name: 'RPM', line: {color: '#f59e0b'} },
                                { x: analysisResults ? analysisResults.is_anomaly.map((anom, i) => anom ? analysisResults.sequence_end_indices[i] : null).filter(x => x && x < currentIndex) : [],
                                    y: analysisResults ? analysisResults.is_anomaly.map((anom, i) => anom ? fullData[analysisResults.sequence_end_indices[i]].RPM : null).filter(x => x !== null) : [],
                                    mode: 'markers', type: 'scatter', name: 'Anomaly', marker: {color: 'red', size: 8} }
                            ]}
                            layout={getLayout('Engine Load & Anomalies')}
                            style={{width: '100%', height: '100%'}}
                            useResizeHandler={true}
                        />
                    </div>
                </div>

                {analysisResults && (
                    <div className="forensics-section">
                        <div className="forensics-header">
                            <h3>Forensics Report</h3>
                            <div className="label-text">Total Events: {analysisResults.is_anomaly.filter(Boolean).length}</div>
                        </div>

                        <div className="forensics-grid">
                            <div className="anomaly-list">
                                {analysisResults.is_anomaly.map((isAnom, idx) => (
                                    isAnom ? (
                                        <div
                                            key={idx}
                                            className={`anomaly-item ${selectedAnomalyIndex === idx ? 'selected' : ''}`}
                                            onClick={() => setSelectedAnomalyIndex(idx)}
                                        >
                                            <div className="metric-label">Event #{idx}</div>
                                            <div className="metric-value" style={{fontSize: '0.9rem'}}>Step {analysisResults.sequence_end_indices[idx]}</div>
                                            <div className="metric-unit text-red">Error: {analysisResults.reconstruction_error[idx].toFixed(4)}</div>
                                        </div>
                                    ) : null
                                ))}
                                {analysisResults.is_anomaly.filter(Boolean).length === 0 && <div className="report-text">No anomalies detected in this lap.</div>}
                            </div>

                            <div className="report-content">
                                {selectedAnomalyIndex !== null && (
                                    <>
                                        {/* [CRITICAL] Rendering the Python-generated explanation directly */}
                                        <div className="report-text" style={{whiteSpace: 'pre-line'}}>
                                            <div style={{marginBottom:'10px', color: '#fff', fontWeight:'bold'}}>PYTHON ENGINE ANALYSIS:</div>
                                            {/* Markdown rendering logic for basic boldness */}
                                            {analysisResults.explanations[selectedAnomalyIndex].split('**').map((part, i) =>
                                                i % 2 === 1 ? <strong key={i}>{part}</strong> : part
                                            )}
                                        </div>

                                        <div className="chart-panel" style={{height: '200px'}}>
                                            <Plot
                                                data={[{
                                                    x: analysisResults.top_features[selectedAnomalyIndex].map(f => f[0]),
                                                    y: analysisResults.top_features[selectedAnomalyIndex].map(f => f[1]),
                                                    type: 'bar',
                                                    marker: {color: '#ef4444'}
                                                }]}
                                                layout={{
                                                    ...getLayout('Root Cause Analysis'),
                                                    margin: {t: 30, b: 30, l: 30, r: 10}
                                                }}
                                                style={{width: '100%', height: '100%'}}
                                                useResizeHandler={true}
                                            />
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                )}

            </main>
        </div>
    );
}

const MetricCard = ({ label, value, unit }) => (
    <div className="metric-card">
        <span className="metric-label">{label}</span>
        <div style={{display: 'flex', alignItems: 'baseline'}}>
            <span className="metric-value">{value}</span>
            <span className="metric-unit">{unit}</span>
        </div>
    </div>
);

export default App;