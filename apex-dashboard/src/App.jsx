import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import TrackMap from './components/TrackMap';
import Logo from './components/Logo.jsx';
import './App.css';

const API_URL = "http://127.0.0.1:8000";
const START_INDEX = 10;

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

// Linear Interpolation Helper
const lerp = (start, end, t) => start * (1 - t) + end * t;

// Angle Interpolation (Handles 359->1 degree crossover)
const lerpAngle = (a, b, t) => {
    const da = (b - a) % 360;
    const distance = 2 * da % 360 - da;
    return a + distance * t;
};

function App() {
    const [view, setView] = useState('dashboard');
    const [config, setConfig] = useState({ year: 2023, gp: "Bahrain", sessionKey: "Race", driver: "PER" });

    const simulationDataRef = useRef([]);
    const [sectorData, setSectorData] = useState(null);
    const [dataLoaded, setDataLoaded] = useState(false);

    // Playback State
    const [isRunning, setIsRunning] = useState(false);
    const [loading, setLoading] = useState(false);
    const [activeAttack, setActiveAttack] = useState(ATTACKS.NONE);
    const [mapMode, setMapMode] = useState('broadcast');

    // Smooth Animation State
    const [floatIndex, setFloatIndex] = useState(START_INDEX);
    const lastFrameTimeRef = useRef(0);
    const requestRef = useRef(null);

    // Metrics for UI
    const [metrics, setMetrics] = useState({ Speed: 0, RPM: 0, nGear: 0, Throttle: 0, Brake: 0, DRS: 0, Distance: 0 });
    const [driverPos, setDriverPos] = useState({ x: 0, y: 0, angle: 0 });

    // Analysis
    const [analysisResults, setAnalysisResults] = useState(null);
    const [selectedAnomalyIndex, setSelectedAnomalyIndex] = useState(null);

    const handleClear = () => {
        setIsRunning(false);
        if (requestRef.current) cancelAnimationFrame(requestRef.current);
        simulationDataRef.current = [];
        setSectorData(null);
        setDataLoaded(false);
        setAnalysisResults(null);
        setSelectedAnomalyIndex(null);
        setFloatIndex(START_INDEX);
        setActiveAttack(ATTACKS.NONE);
        setMetrics({ Speed: 0, RPM: 0, nGear: 0, Throttle: 0, Brake: 0, DRS: 0, Distance: 0 });
    };

    const handleLoadData = async () => {
        handleClear();
        setLoading(true);
        try {
            const sessionCode = SESSION_OPTIONS[config.sessionKey];
            const res = await axios.post(`${API_URL}/load_data`, { ...config, session: sessionCode });

            if (res.data && Array.isArray(res.data.telemetry)) {
                simulationDataRef.current = res.data.telemetry;
                setSectorData(res.data.sectors);
                setDataLoaded(true);
                setFloatIndex(START_INDEX);
            }
        } catch (err) {
            console.error(err);
            alert(`Error loading data: ${err.response?.data?.detail || err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const applyAttackVector = (dataPoint) => {
        if (!activeAttack) return dataPoint;
        let modifiedPoint = { ...dataPoint };
        switch (activeAttack) {
            case ATTACKS.JAM_RPM: modifiedPoint.RPM = 0; break;
            case ATTACKS.DRIFT_THROTTLE: modifiedPoint.Throttle = Math.min(100, modifiedPoint.Throttle + 10); break;
            case ATTACKS.SPOOF_GPS: modifiedPoint.X += 2000; modifiedPoint.Y += 2000; break;
            default: break;
        }
        return modifiedPoint;
    };

    // --- 120Hz ANIMATION LOOP ---
    const animate = (time) => {
        if (!lastFrameTimeRef.current) lastFrameTimeRef.current = time;
        const deltaTime = time - lastFrameTimeRef.current;
        lastFrameTimeRef.current = time;

        // Playback speed: 10 data points per second (approx)
        // 10Hz data = 100ms per point.
        // We want to advance floatIndex by (deltaTime / 100)
        const speedFactor = 1.5; // Speed multiplier
        const indexIncrement = (deltaTime / 100) * speedFactor;

        setFloatIndex(prev => {
            const nextIdx = prev + indexIncrement;

            if (nextIdx >= simulationDataRef.current.length - 2) {
                setIsRunning(false);
                return prev;
            }

            // Interpolation Logic
            const idxFloor = Math.floor(nextIdx);
            const t = nextIdx - idxFloor; // Fractional part (0.0 - 1.0)

            const currData = simulationDataRef.current[idxFloor];
            const nextData = simulationDataRef.current[idxFloor + 1];

            if (currData && nextData) {
                // Interpolate Metrics
                const interpolated = {
                    Speed: lerp(currData.Speed, nextData.Speed, t),
                    RPM: lerp(currData.RPM, nextData.RPM, t),
                    Throttle: lerp(currData.Throttle, nextData.Throttle, t),
                    Brake: lerp(currData.Brake, nextData.Brake, t),
                    nGear: currData.nGear, // Gears don't interpolate
                    DRS: currData.DRS,
                    Distance: lerp(currData.Distance, nextData.Distance, t),
                    X: lerp(currData.X, nextData.X, t),
                    Y: lerp(currData.Y, nextData.Y, t)
                };

                // Attack Injection
                const finalMetrics = applyAttackVector(interpolated);
                setMetrics(finalMetrics);

                // Calculate Smooth Angle
                const angleCurr = Math.atan2(nextData.Y - currData.Y, nextData.X - currData.X) * (180 / Math.PI);
                setDriverPos({ x: finalMetrics.X, y: finalMetrics.Y, angle: angleCurr });
            }

            return nextIdx;
        });

        requestRef.current = requestAnimationFrame(animate);
    };

    useEffect(() => {
        if (isRunning && dataLoaded) {
            lastFrameTimeRef.current = 0;
            requestRef.current = requestAnimationFrame(animate);
        } else if (requestRef.current) {
            cancelAnimationFrame(requestRef.current);
        }
        return () => { if (requestRef.current) cancelAnimationFrame(requestRef.current); };
    }, [isRunning, dataLoaded, activeAttack]); // Re-bind if attack changes to apply immediately

    const handleRunAnalysis = async () => {
        if (!simulationDataRef.current.length) return;
        setLoading(true);
        try {
            const metaPayload = { ...config, session: config.sessionKey };
            const payload = {
                Speed: simulationDataRef.current.map(d => d.Speed),
                RPM: simulationDataRef.current.map(d => d.RPM),
                Throttle: simulationDataRef.current.map(d => d.Throttle),
                Brake: simulationDataRef.current.map(d => d.Brake),
                nGear: simulationDataRef.current.map(d => d.nGear),
                DRS: simulationDataRef.current.map(d => d.DRS),
                metadata: metaPayload
            };
            const res = await axios.post(`${API_URL}/predict`, payload);
            setAnalysisResults(res.data);
            const firstAnom = res.data.is_anomaly.findIndex(x => x === true);
            if (firstAnom !== -1) {
                setSelectedAnomalyIndex(firstAnom);
                alert(`Forensics: ${res.data.is_anomaly.filter(Boolean).length} Events Found.`);
            } else {
                alert("Clean Lap. No Anomalies.");
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // --- CHART DATA PREP ---
    // We slice the history up to the floor index, then ADD the interpolated current point for smoothness
    const vizIndex = Math.floor(floatIndex);
    const vizData = simulationDataRef.current;

    // Optimized chart data construction
    const getChartData = (field, color) => {
        if (!dataLoaded) return [];
        const historyX = Array.from({length: vizIndex}, (_, i) => i);
        const historyY = vizData.slice(0, vizIndex).map(d => d[field]);

        // Add smooth tip
        historyX.push(floatIndex);
        historyY.push(metrics[field]);

        return [{
            x: historyX, y: historyY,
            type: 'scatter', mode: 'lines', name: field,
            line: { color: color, width: 2 }
        }];
    };

    // Common Chart Layout
    const chartLayout = {
        autosize: true,
        margin: { t: 5, r: 10, l: 30, b: 20 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        showlegend: false,
        xaxis: { showgrid: true, gridcolor: '#f1f5f9', zeroline: false, color: '#94a3b8', tickfont: { family: 'JetBrains Mono', size: 9 } },
        yaxis: { showgrid: true, gridcolor: '#f1f5f9', gridwidth: 1, zeroline: false, color: '#94a3b8', tickfont: { family: 'JetBrains Mono', size: 9 } },
        font: { family: 'Inter', color: '#0f172a' }
    };

    return (
        <div className="app-container">
            <aside className="sidebar">
                <div className="brand">
                    <Logo width={28} height={28} />
                    <span style={{color: '#2563eb'}}>APEX</span>SENTINEL
                </div>

                {view === 'forensics' ? (
                    <button className="btn btn-outline" onClick={() => setView('dashboard')}>← BACK TO LIVE</button>
                ) : (
                    <>
                        <div className="control-section">
                            <span className="section-label">CONFIGURATION</span>
                            <input className="input-field" type="number" min="2018" max="2025" value={config.year} onChange={e => setConfig({...config, year: parseInt(e.target.value)})} placeholder="Year" />
                            <input className="input-field" value={config.gp} onChange={e => setConfig({...config, gp: e.target.value})} placeholder="Grand Prix" />
                            <select className="select-field" value={config.sessionKey} onChange={e => setConfig({...config, sessionKey: e.target.value})}>
                                {Object.keys(SESSION_OPTIONS).map(opt => <option key={opt} value={opt}>{opt}</option>)}
                            </select>
                            <input className="input-field" value={config.driver} onChange={e => setConfig({...config, driver: e.target.value})} placeholder="Driver" />
                            <button className="btn btn-primary" onClick={handleLoadData} disabled={loading}>{loading ? "SYNCING..." : "LOAD SESSION"}</button>
                        </div>

                        <div className="control-section" style={{borderTop: '1px solid #cbd5e1', paddingTop: '20px'}}>
                            <span className="section-label" style={{color: '#dc2626'}}>RED TEAM OPS</span>
                            <button className={`btn ${activeAttack === ATTACKS.JAM_RPM ? 'btn-primary' : 'btn-outline'}`} onClick={() => setActiveAttack(activeAttack === ATTACKS.JAM_RPM ? null : ATTACKS.JAM_RPM)} style={activeAttack === ATTACKS.JAM_RPM ? {background: '#dc2626', borderColor: '#dc2626'} : {}}>
                                {activeAttack === ATTACKS.JAM_RPM ? '⚠ SENSOR JAMMED' : 'JAM RPM SENSOR'}
                            </button>
                            <button className={`btn ${activeAttack === ATTACKS.DRIFT_THROTTLE ? 'btn-primary' : 'btn-outline'}`} onClick={() => setActiveAttack(activeAttack === ATTACKS.DRIFT_THROTTLE ? null : ATTACKS.DRIFT_THROTTLE)} style={activeAttack === ATTACKS.DRIFT_THROTTLE ? {background: '#dc2626', borderColor: '#dc2626'} : {}}>
                                {activeAttack === ATTACKS.DRIFT_THROTTLE ? '⚠ INJECTING DRIFT' : 'DRIFT THROTTLE'}
                            </button>
                            <button className={`btn ${activeAttack === ATTACKS.SPOOF_GPS ? 'btn-primary' : 'btn-outline'}`} onClick={() => setActiveAttack(activeAttack === ATTACKS.SPOOF_GPS ? null : ATTACKS.SPOOF_GPS)} style={activeAttack === ATTACKS.SPOOF_GPS ? {background: '#dc2626', borderColor: '#dc2626'} : {}}>
                                {activeAttack === ATTACKS.SPOOF_GPS ? '⚠ SPOOFING GPS' : 'SPOOF GPS'}
                            </button>
                        </div>

                        <div className="control-section" style={{marginTop: 'auto'}}>
                            <span className="section-label">PLAYBACK</span>
                            <div className="sim-controls">
                                <button className="btn btn-green" onClick={() => setIsRunning(!isRunning)} disabled={!dataLoaded}>{isRunning ? "HALT" : "RUN"}</button>
                                <button className="btn btn-outline" style={{width: '50px'}} onClick={handleClear} title="Reset">↻</button>
                            </div>
                            <button className="btn btn-outline" onClick={handleRunAnalysis} disabled={!dataLoaded}>ANALYZE LOGS</button>
                            {analysisResults && <button className="btn btn-primary" onClick={() => setView('forensics')}>VIEW REPORT →</button>}
                        </div>
                    </>
                )}

                <div className="status-badge">
                    <span>SYSTEM READY</span>
                    <div className={`status-dot ${isRunning ? 'active' : ''}`} />
                </div>
            </aside>

            <main className="main-content">
                {view === 'dashboard' ? (
                    <>
                        <div className="top-bar">
                            <div className="session-tag">
                                {isRunning && <span className="live-indicator">●</span>}
                                {dataLoaded ? `${config.year} ${config.gp.toUpperCase()} // ${config.driver}` : "AWAITING DATALINK"}
                                {activeAttack && <span style={{marginLeft: '15px', color: '#dc2626', background: '#fef2f2', padding: '2px 8px', fontSize: '11px', borderRadius: '4px', border: '1px solid #fee2e2', fontWeight: 700}}>⚠ INTRUSION DETECTED</span>}
                            </div>
                            <div className="timer">T+{(floatIndex * 0.1).toFixed(2)}s</div>
                        </div>

                        <div className="dashboard-view">
                            <div className="metrics-row">
                                <MetricCard label="SPEED" value={Math.round(metrics.Speed)} unit="KM/H" />
                                <MetricCard label="RPM" value={Math.round(metrics.RPM)} unit="RPM" color={activeAttack === ATTACKS.JAM_RPM ? '#dc2626' : undefined} />
                                <MetricCard label="THROTTLE" value={Math.round(metrics.Throttle)} unit="%" color={activeAttack === ATTACKS.DRIFT_THROTTLE ? '#dc2626' : '#16a34a'} />
                                <MetricCard label="BRAKE" value={Math.round(metrics.Brake)} unit="%" />
                                <MetricCard label="GEAR" value={metrics.nGear} unit="" />
                                <MetricCard label="DRS" value={metrics.DRS >= 10 ? "OPEN" : (metrics.DRS === 8 ? "RDY" : "CLS")} unit="" color={metrics.DRS >= 10 ? '#16a34a' : (metrics.DRS === 8 ? '#ca8a04' : undefined)} />
                            </div>

                            <div className="main-stage">
                                <div className="map-panel">
                                    <TrackMap
                                        fullData={vizData}
                                        anomalies={analysisResults ? analysisResults.is_anomaly.map((isAnom, i) => isAnom ? analysisResults.sequence_end_indices[i] : null).filter(i => i !== null) : []}
                                        mapMode={mapMode}
                                        realSectors={sectorData}
                                        driverPosition={driverPos}
                                        currentDistance={metrics.Distance}
                                    />
                                    <div style={{position: 'absolute', bottom: '20px', right: '20px', display: 'flex', gap: '8px', zIndex: 10}}>
                                        <button onClick={() => setMapMode('broadcast')} style={{background: mapMode === 'broadcast' ? '#2563eb' : '#fff', color: mapMode === 'broadcast' ? '#fff' : '#475569', border: '1px solid #cbd5e1', padding: '6px 12px', fontSize: '11px', fontWeight: 'bold', borderRadius: '4px', cursor: 'pointer'}}>TV</button>
                                        <button onClick={() => setMapMode('engineering')} style={{background: mapMode === 'engineering' ? '#2563eb' : '#fff', color: mapMode === 'engineering' ? '#fff' : '#475569', border: '1px solid #cbd5e1', padding: '6px 12px', fontSize: '11px', fontWeight: 'bold', borderRadius: '4px', cursor: 'pointer'}}>ENG</button>
                                    </div>
                                </div>

                                <div className="telemetry-grid">
                                    <div className="chart-box">
                                        <div className="chart-header">VELOCITY / INPUT</div>
                                        <Plot
                                            data={[
                                                ...getChartData('Speed', '#2563eb'),
                                                ...getChartData('Throttle', '#16a34a').map(t => ({...t, yaxis: 'y2'}))
                                            ]}
                                            layout={{ ...chartLayout, yaxis2: { overlaying: 'y', side: 'right', showgrid: false } }}
                                            style={{width: '100%', height: '100%'}}
                                            config={{displayModeBar: false}}
                                        />
                                    </div>
                                    <div className="chart-box">
                                        <div className="chart-header">RPM</div>
                                        <Plot
                                            data={getChartData('RPM', '#ca8a04')}
                                            layout={chartLayout}
                                            style={{width: '100%', height: '100%'}}
                                            config={{displayModeBar: false}}
                                        />
                                    </div>
                                    <div className="chart-box">
                                        <div className="chart-header">BRAKE PRESSURE</div>
                                        <Plot
                                            data={getChartData('Brake', '#dc2626')}
                                            layout={chartLayout}
                                            style={{width: '100%', height: '100%'}}
                                            config={{displayModeBar: false}}
                                        />
                                    </div>
                                    <div className="chart-box">
                                        <div className="chart-header">GEAR</div>
                                        <Plot
                                            data={getChartData('nGear', '#64748b').map(t => ({...t, line: {...t.line, shape:'hv'}}))} // Stepped line for gears
                                            layout={chartLayout}
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
                        {/* FORENSICS SIDEBAR */}
                        <div className="forensics-sidebar">
                            <div className="list-header">
                                <span>DETECTED EVENTS</span>
                                <span style={{fontSize:'12px', color:'#64748b'}}>{analysisResults.is_anomaly.filter(Boolean).length} TOTAL</span>
                            </div>
                            <div className="event-list">
                                {analysisResults.is_anomaly.map((isAnom, idx) => (
                                    isAnom ? (
                                        <div key={idx} className={`event-row ${selectedAnomalyIndex === idx ? 'active' : ''}`} onClick={() => setSelectedAnomalyIndex(idx)}>
                                            <div className="event-main">
                                                <span>EVENT ID #{idx}</span>
                                                <span style={{color: analysisResults.classifications?.[idx].includes("CRITICAL") ? '#dc2626' : '#ca8a04'}}>
                                                    {analysisResults.classifications?.[idx].includes("DROPOUT") ? "CRITICAL" : "WARN"}
                                                </span>
                                            </div>
                                            <div className="event-sub">T+{analysisResults.sequence_end_indices[idx] * 0.1}s | ERR: {analysisResults.reconstruction_error[idx].toFixed(4)}</div>
                                        </div>
                                    ) : null
                                ))}
                            </div>
                        </div>

                        {/* FORENSICS DETAIL */}
                        <div className="report-detail">
                            {selectedAnomalyIndex !== null && analysisResults ? (
                                <div className="report-card">
                                    <div className="report-header-strip">
                                        <div className="report-id">
                                            REPORT #APX-{config.year}-{selectedAnomalyIndex.toString().padStart(4, '0')}
                                        </div>
                                        <div className="report-badge">
                                            {analysisResults.classifications[selectedAnomalyIndex]}
                                        </div>
                                    </div>

                                    <div className="report-body">
                                        <div className="report-grid">
                                            <div className="stat-box">
                                                <div className="stat-label">RECONSTRUCTION ERROR</div>
                                                <div className="stat-value" style={{color: '#dc2626'}}>
                                                    {analysisResults.reconstruction_error[selectedAnomalyIndex].toFixed(6)}
                                                </div>
                                                <div style={{fontSize:'10px', color:'#64748b', marginTop:'4px'}}>
                                                    THRESHOLD: {analysisResults.threshold.toFixed(6)}
                                                </div>
                                            </div>
                                            <div className="stat-box">
                                                <div className="stat-label">RISK ASSESSMENT</div>
                                                <div className="stat-value">
                                                    {analysisResults.classifications[selectedAnomalyIndex].includes("DROPOUT") ? "HIGH" : "MEDIUM"}
                                                </div>
                                            </div>
                                        </div>

                                        <div>
                                            <div className="section-label" style={{marginBottom:'10px'}}>PRIMARY INDICATORS</div>
                                            <table className="indicator-table">
                                                <thead>
                                                <tr>
                                                    <th>CHANNEL</th>
                                                    <th>DEVIATION SCORE</th>
                                                    <th>CONTRIBUTION</th>
                                                </tr>
                                                </thead>
                                                <tbody>
                                                {analysisResults.top_features[selectedAnomalyIndex].map((feat, i) => (
                                                    <tr key={i}>
                                                        <td style={{fontWeight:'700'}}>{feat[0]}</td>
                                                        <td>{feat[1].toFixed(4)}</td>
                                                        <td>
                                                            <div className="bar-container">
                                                                <div className="bar-fill" style={{width: `${Math.min(100, feat[1] * 500)}%`}}></div>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                                </tbody>
                                            </table>
                                        </div>

                                        {analysisResults.secure_receipts && analysisResults.secure_receipts[selectedAnomalyIndex] && (
                                            <div className="chain-box">
                                                <div className="chain-icon">🔒</div>
                                                <div className="chain-info">
                                                    <span style={{fontWeight:'700', fontSize:'10px', opacity:0.8}}>CHAIN OF CUSTODY SECURED</span>
                                                    <span>ID: {analysisResults.secure_receipts[selectedAnomalyIndex].id}</span>
                                                    <span className="hash">SHA: {analysisResults.secure_receipts[selectedAnomalyIndex].hash.substring(0, 40)}...</span>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : <div style={{display:'flex', height:'100%', alignItems:'center', justifyContent:'center', color:'#94a3b8'}}>SELECT AN EVENT TO DECRYPT</div>}
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
        <span className="metric-val" style={{color: color || '#0f172a'}}>{value}</span>
        <span className="metric-unit">{unit}</span>
    </div>
);

export default App;