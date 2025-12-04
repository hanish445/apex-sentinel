import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import TrackMap from './components/TrackMap';
import Logo from './components/Logo.jsx';
import './App.css';

const API_URL = "http://127.0.0.1:8000";
const TIMESTEPS = 10;

const SESSION_OPTIONS = {
    'Race': 'R', 'Qualifying': 'Q', 'Sprint': 'S',
    'FP1': 'FP1', 'FP2': 'FP2', 'FP3': 'FP3'
};

const ATTACKS = {
    NONE: null,
    JAM_RPM: 'JAM_RPM',
    DRIFT_THROTTLE: 'DRIFT',
    SPOOF_GPS: 'SPOOF_GPS'
};

function App() {
    const [view, setView] = useState('dashboard');
    const [config, setConfig] = useState({ year: 2023, gp: "Bahrain", sessionKey: "Race", driver: "PER" });

    const simulationDataRef = useRef([]);
    const [sectorData, setSectorData] = useState(null);
    const [dataLoaded, setDataLoaded] = useState(false);

    const [currentIndex, setCurrentIndex] = useState(TIMESTEPS);
    const [isRunning, setIsRunning] = useState(false);
    const [loading, setLoading] = useState(false);

    const [activeAttack, setActiveAttack] = useState(ATTACKS.NONE);
    const [mapMode, setMapMode] = useState('broadcast');

    const [metrics, setMetrics] = useState({ Speed: 0, RPM: 0, nGear: 0, Throttle: 0, Brake: 0, DRS: 0 });
    const [analysisResults, setAnalysisResults] = useState(null);
    const [selectedAnomalyIndex, setSelectedAnomalyIndex] = useState(null);

    const handleClear = () => {
        setIsRunning(false);
        simulationDataRef.current = [];
        setSectorData(null);
        setDataLoaded(false);
        setAnalysisResults(null);
        setSelectedAnomalyIndex(null);
        setCurrentIndex(TIMESTEPS);
        setActiveAttack(ATTACKS.NONE);
        setMetrics({ Speed: 0, RPM: 0, nGear: 0, Throttle: 0, Brake: 0, DRS: 0 });
    };

    const handleLoadData = async () => {
        handleClear();
        setLoading(true);
        try {
            const sessionCode = SESSION_OPTIONS[config.sessionKey];
            const payload = { ...config, session: sessionCode };

            const res = await axios.post(`${API_URL}/load_data`, payload);

            // [CRASH FIX] Validation check
            if (res.data && Array.isArray(res.data.telemetry)) {
                simulationDataRef.current = res.data.telemetry;
                setSectorData(res.data.sectors);
                setDataLoaded(true);
                setCurrentIndex(TIMESTEPS);
            } else if (Array.isArray(res.data)) {
                // Fallback for old API format
                simulationDataRef.current = res.data;
                setDataLoaded(true);
                setCurrentIndex(TIMESTEPS);
            } else {
                throw new Error("Invalid data format received from API");
            }

        } catch (err) {
            console.error(err);
            alert(`Error loading data: ${err.response?.data?.detail || err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleRunAnalysis = async () => {
        if (!simulationDataRef.current.length) return;
        setLoading(true);
        try {
            const currentData = simulationDataRef.current;

            // Send proper session name for metadata
            const metaPayload = { ...config, session: config.sessionKey };

            const payload = {
                Speed: currentData.map(d => d.Speed),
                RPM: currentData.map(d => d.RPM),
                Throttle: currentData.map(d => d.Throttle),
                Brake: currentData.map(d => d.Brake),
                nGear: currentData.map(d => d.nGear),
                DRS: currentData.map(d => d.DRS),
                metadata: metaPayload
            };

            const res = await axios.post(`${API_URL}/predict`, payload);
            setAnalysisResults(res.data);

            const firstAnom = res.data.is_anomaly.findIndex(x => x === true);
            if (firstAnom !== -1) {
                setSelectedAnomalyIndex(firstAnom);
                alert(`Forensics Complete: ${res.data.is_anomaly.filter(Boolean).length} Events Detected.`);
            } else {
                alert("Forensics Complete: Zero Anomalies Found.");
            }

        } catch (err) {
            alert("Analysis failed. Is backend running?");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const applyAttackVector = (dataPoint) => {
        if (!activeAttack) return dataPoint;
        let modifiedPoint = { ...dataPoint };

        switch (activeAttack) {
            case ATTACKS.JAM_RPM:
                modifiedPoint.RPM = 0;
                break;
            case ATTACKS.DRIFT_THROTTLE:
                modifiedPoint.Throttle = Math.min(100, modifiedPoint.Throttle + 10);
                break;
            case ATTACKS.SPOOF_GPS:
                modifiedPoint.X = modifiedPoint.X + 2000;
                modifiedPoint.Y = modifiedPoint.Y + 2000;
                break;
            default: break;
        }
        return modifiedPoint;
    };

    useEffect(() => {
        let interval;
        if (isRunning && dataLoaded && currentIndex < simulationDataRef.current.length) {
            interval = setInterval(() => {
                setCurrentIndex(prev => {
                    const nextIndex = prev + 1;
                    if (nextIndex >= simulationDataRef.current.length) {
                        setIsRunning(false);
                        return prev;
                    }
                    let currentPacket = simulationDataRef.current[nextIndex];
                    if (activeAttack) {
                        const poisonedPacket = applyAttackVector(currentPacket);
                        simulationDataRef.current[nextIndex] = poisonedPacket;
                        currentPacket = poisonedPacket;
                    }
                    setMetrics(currentPacket);
                    return nextIndex;
                });
            }, 50);
        }
        return () => clearInterval(interval);
    }, [isRunning, currentIndex, dataLoaded, activeAttack]);

    const getTagColor = (tag) => {
        if (!tag) return "#a1a1aa";
        if (tag.includes("LOCK-UP") || tag.includes("TRACTION")) return "#eab308";
        if (tag.includes("SENSOR") || tag.includes("FAULT") || tag.includes("CRITICAL")) return "#ef4444";
        return "#a1a1aa";
    };

    const getLayout = () => ({
        autosize: true,
        margin: { t: 5, r: 10, l: 30, b: 20 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        showlegend: false,
        xaxis: { showgrid: false, zeroline: false, color: '#52525b', tickfont: { family: 'JetBrains Mono', size: 9 } },
        yaxis: { showgrid: true, gridcolor: '#27272a', gridwidth: 1, zeroline: false, color: '#52525b', tickfont: { family: 'JetBrains Mono', size: 9 } },
        font: { family: 'Inter', color: '#f8fafc' }
    });

    const vizData = simulationDataRef.current;

    return (
        <div className="app-container">
            {view === 'dashboard' && (
                <aside className="sidebar">
                    <div className="brand">
                        <Logo width={32} height={32} />
                        <div><span style={{color: '#fff'}}>APEX</span><span style={{color: '#e10600'}}>SENTINEL</span></div>
                    </div>

                    <div className="control-section">
                        <div className="section-label">CONFIGURATION</div>
                        <input className="input-field" type="number" min="2018" max="2025" value={config.year} onChange={e => setConfig({...config, year: parseInt(e.target.value)})} placeholder="Year" />
                        <input className="input-field" value={config.gp} onChange={e => setConfig({...config, gp: e.target.value})} placeholder="Grand Prix" />
                        <select className="select-field" value={config.sessionKey} onChange={e => setConfig({...config, sessionKey: e.target.value})}>
                            {Object.keys(SESSION_OPTIONS).map(opt => <option key={opt} value={opt}>{opt}</option>)}
                        </select>
                        <input className="input-field" value={config.driver} onChange={e => setConfig({...config, driver: e.target.value})} placeholder="Driver" />
                        <button className="btn btn-primary" onClick={handleLoadData} disabled={loading}>{loading ? "DOWNLOADING..." : "LOAD DATA"}</button>
                    </div>

                    <div className="control-section" style={{borderTop: '1px solid #2d323b', paddingTop: '15px'}}>
                        <div className="section-label" style={{color: '#ef4444'}}>RED TEAM // INJECTION</div>
                        <div className="sim-controls" style={{flexDirection: 'column', gap: '8px'}}>
                            <button className={`btn ${activeAttack === ATTACKS.JAM_RPM ? 'btn-primary' : 'btn-outline'}`} onClick={() => setActiveAttack(activeAttack === ATTACKS.JAM_RPM ? null : ATTACKS.JAM_RPM)} style={{fontSize: '11px', padding: '10px'}}>
                                {activeAttack === ATTACKS.JAM_RPM ? '⚠ JAMMING RPM...' : 'JAM RPM SENSOR'}
                            </button>
                            <button className={`btn ${activeAttack === ATTACKS.DRIFT_THROTTLE ? 'btn-primary' : 'btn-outline'}`} onClick={() => setActiveAttack(activeAttack === ATTACKS.DRIFT_THROTTLE ? null : ATTACKS.DRIFT_THROTTLE)} style={{fontSize: '11px', padding: '10px'}}>
                                {activeAttack === ATTACKS.DRIFT_THROTTLE ? '⚠ INJECTING BIAS...' : 'INJECT THROTTLE BIAS'}
                            </button>
                            <button className={`btn ${activeAttack === ATTACKS.SPOOF_GPS ? 'btn-primary' : 'btn-outline'}`} onClick={() => setActiveAttack(activeAttack === ATTACKS.SPOOF_GPS ? null : ATTACKS.SPOOF_GPS)} style={{fontSize: '11px', padding: '10px'}}>
                                {activeAttack === ATTACKS.SPOOF_GPS ? '⚠ SPOOFING POS...' : 'SPOOF GPS SIGNAL'}
                            </button>
                        </div>
                    </div>

                    <div className="control-section">
                        <div className="section-label">SIMULATION</div>
                        <div className="sim-controls">
                            <button className="btn btn-green" onClick={() => setIsRunning(!isRunning)} disabled={!dataLoaded}>{isRunning ? "PAUSE" : "PLAY"}</button>
                            <button className="btn btn-outline" style={{width: '60px'}} onClick={handleClear} title="Clear">🗑️</button>
                        </div>
                    </div>
                    <div className="control-section" style={{marginTop: 'auto'}}>
                        <button className="btn btn-outline" onClick={handleRunAnalysis} disabled={!dataLoaded}>RUN DIAGNOSTICS</button>
                        {analysisResults && <button className="btn btn-primary" style={{marginTop: '10px'}} onClick={() => setView('forensics')}>OPEN REPORT →</button>}
                    </div>
                    <div className="status-badge"><span>SYSTEM STATUS</span><div className={`status-dot ${isRunning ? 'active' : ''}`} /></div>
                </aside>
            )}

            <main className="main-content">
                {view === 'dashboard' ? (
                    <>
                        <div className="top-bar">
                            <div className="session-tag">
                                {isRunning && <span className="live-indicator">●</span>}
                                {dataLoaded ? `${config.year} ${config.gp} // ${config.driver}` : "NO DATA"}
                                {activeAttack && <span style={{marginLeft: '15px', color: '#ef4444', border: '1px solid #ef4444', padding: '2px 6px', fontSize: '10px', borderRadius: '4px'}}>⚠ ATTACK ACTIVE: {activeAttack}</span>}
                            </div>
                            <div className="timer">T+{(currentIndex * 0.1).toFixed(1)}s</div>
                        </div>

                        <div className="dashboard-view">
                            <div className="metrics-row">
                                <MetricCard label="SPEED" value={Math.round(metrics.Speed)} unit="KM/H" />
                                <MetricCard label="RPM" value={Math.round(metrics.RPM)} unit="RPM" color={activeAttack === ATTACKS.JAM_RPM ? '#ef4444' : '#eab308'} />
                                <MetricCard label="THROTTLE" value={Math.round(metrics.Throttle)} unit="%" color={activeAttack === ATTACKS.DRIFT_THROTTLE ? '#ef4444' : '#22c55e'} />
                                <MetricCard label="BRAKE" value={Math.round(metrics.Brake)} unit="%" color="#ef4444" />
                                <MetricCard label="GEAR" value={metrics.nGear} unit="" color="#3b82f6" />
                                <div className="metric-card">
                                    <span className="metric-label">DRS STATUS</span>
                                    <span className="metric-val" style={{color: metrics.DRS >= 10 ? '#22c55e' : (metrics.DRS === 8 ? '#eab308' : '#52525b'), fontSize: '18px'}}>
                                        {metrics.DRS >= 10 ? "OPEN" : (metrics.DRS === 8 ? "READY" : "CLOSED")}
                                    </span>
                                </div>
                            </div>

                            <div className="main-stage">
                                <div className="map-panel">
                                    <TrackMap fullData={vizData} currentIndex={currentIndex} anomalies={analysisResults ? analysisResults.is_anomaly.map((isAnom, i) => isAnom ? analysisResults.sequence_end_indices[i] : null).filter(i => i !== null) : []} mapMode={mapMode} realSectors={sectorData} />
                                    <div style={{position: 'absolute', bottom: '15px', right: '15px', display: 'flex', gap: '5px', zIndex: 10}}>
                                        <button onClick={() => setMapMode('broadcast')} style={{background: mapMode === 'broadcast' ? '#a855f7' : 'rgba(0,0,0,0.5)', color: '#fff', border: '1px solid #3f3f46', padding: '6px 12px', fontSize: '10px', fontFamily: 'Rajdhani', fontWeight: 'bold', cursor: 'pointer'}}>TV MODE</button>
                                        <button onClick={() => setMapMode('engineering')} style={{background: mapMode === 'engineering' ? '#00d2be' : 'rgba(0,0,0,0.5)', color: mapMode === 'engineering' ? '#000' : '#fff', border: '1px solid #3f3f46', padding: '6px 12px', fontSize: '10px', fontFamily: 'Rajdhani', fontWeight: 'bold', cursor: 'pointer'}}>ENG MODE</button>
                                    </div>
                                </div>

                                <div className="telemetry-grid">
                                    <div className="chart-box">
                                        <div className="chart-header">SPEED & THROTTLE</div>
                                        <Plot
                                            data={[
                                                { x: vizData.slice(0, currentIndex).map((_, i) => i), y: vizData.slice(0, currentIndex).map(d => d.Speed), type: 'scatter', mode: 'lines', name: 'Speed', line: {color: '#3b82f6', width: 2} },
                                                { x: vizData.slice(0, currentIndex).map((_, i) => i), y: vizData.slice(0, currentIndex).map(d => d.Throttle), type: 'scatter', mode: 'lines', name: 'Throttle', line: {color: '#22c55e', width: 1}, yaxis: 'y2' }
                                            ]}
                                            layout={{ ...getLayout(), yaxis2: { overlaying: 'y', side: 'right', showgrid: false } }}
                                            style={{width: '100%', height: '100%'}}
                                            config={{displayModeBar: false}}
                                        />
                                    </div>
                                    <div className="chart-box">
                                        <div className="chart-header">ENGINE RPM</div>
                                        <Plot
                                            data={[{ x: vizData.slice(0, currentIndex).map((_, i) => i), y: vizData.slice(0, currentIndex).map(d => d.RPM), type: 'scatter', mode: 'lines', name: 'RPM', line: {color: '#eab308', width: 1.5} }]}
                                            layout={getLayout()}
                                            style={{width: '100%', height: '100%'}}
                                            config={{displayModeBar: false}}
                                        />
                                    </div>
                                    <div className="chart-box">
                                        <div className="chart-header">BRAKE PRESSURE</div>
                                        <Plot
                                            data={[{ x: vizData.slice(0, currentIndex).map((_, i) => i), y: vizData.slice(0, currentIndex).map(d => d.Brake), type: 'scatter', mode: 'lines', name: 'Brake', fill: 'tozeroy', line: {color: '#ef4444', width: 1.5} }]}
                                            layout={getLayout()}
                                            style={{width: '100%', height: '100%'}}
                                            config={{displayModeBar: false}}
                                        />
                                    </div>
                                    <div className="chart-box">
                                        <div className="chart-header">GEAR POSITION</div>
                                        <Plot
                                            data={[{ x: vizData.slice(0, currentIndex).map((_, i) => i), y: vizData.slice(0, currentIndex).map(d => d.nGear), type: 'scatter', mode: 'lines', step: 'hv', name: 'Gear', line: {color: '#a855f7', width: 1.5} }]}
                                            layout={getLayout()}
                                            style={{width: '100%', height: '100%'}}
                                            config={{displayModeBar: false}}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="forensics-view">
                        <div className="forensics-sidebar">
                            <div className="list-header">
                                <button className="btn btn-outline" style={{width:'auto'}} onClick={() => setView('dashboard')}>← BACK</button>
                                <span>{analysisResults.is_anomaly.filter(Boolean).length} EVENTS</span>
                            </div>
                            <div className="event-list">
                                {analysisResults.is_anomaly.map((isAnom, idx) => (
                                    isAnom ? (
                                        <div key={idx} className={`event-row ${selectedAnomalyIndex === idx ? 'active' : ''}`} onClick={() => setSelectedAnomalyIndex(idx)}>
                                            <div className="event-main">
                                                <span>EVENT #{idx}</span>
                                                <span style={{fontSize: '10px', padding: '2px 6px', borderRadius: '2px', fontWeight: '700', color: getTagColor(analysisResults.classifications?.[idx]), background: `${getTagColor(analysisResults.classifications?.[idx])}20`, border: `1px solid ${getTagColor(analysisResults.classifications?.[idx])}40`}}>
                                                    {analysisResults.classifications ? analysisResults.classifications[idx] : "ANOMALY"}
                                                </span>
                                            </div>
                                            <div className="event-sub">TIMESTEP {analysisResults.sequence_end_indices[idx]} | ERR: {analysisResults.reconstruction_error[idx].toFixed(2)}</div>
                                        </div>
                                    ) : null
                                ))}
                            </div>
                        </div>
                        <div className="report-detail">
                            {selectedAnomalyIndex !== null ? (
                                <>
                                    <div className="report-title"><h1>Anomaly Report #{selectedAnomalyIndex}</h1></div>
                                    <div className="analysis-block">
                                        <div className="block-label">AUTOMATED INTERPRETATION</div>
                                        <div className="text-content">
                                            {analysisResults.explanations[selectedAnomalyIndex].split('**').map((part, i) =>
                                                i % 2 === 1 ? <strong key={i} style={{color: '#eab308'}}>{part}</strong> : part
                                            )}
                                        </div>
                                    </div>
                                    <div className="chart-box" style={{height: '500px'}}>
                                        <div className="chart-header">ROOT CAUSE ANALYSIS</div>
                                        <Plot
                                            data={[{ x: analysisResults.top_features[selectedAnomalyIndex].map(f => f[0]), y: analysisResults.top_features[selectedAnomalyIndex].map(f => f[1]), type: 'bar', marker: {color: '#ef4444'} }]}
                                            layout={{...getLayout(), margin: {t: 20, b: 30, l: 30, r: 10}}}
                                            style={{width: '100%', height: '100%'}}
                                            config={{displayModeBar: false}}
                                        />
                                    </div>
                                </>
                            ) : <div className="empty-placeholder">Select an event from the sidebar</div>}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

const MetricCard = ({ label, value, unit, color }) => (
    <div className="metric-card">
        <span className="metric-label">{label}</span>
        <span className="metric-val" style={{color: color || '#fff'}}>{value}</span>
        <span className="metric-unit">{unit}</span>
    </div>
);

export default App;