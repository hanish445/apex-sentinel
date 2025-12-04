import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

// Now accepts 'driverPosition' and 'currentDistance' directly for smooth animation
const TrackMap = ({ fullData, anomalies, mapMode, realSectors, driverPosition, currentDistance }) => {

    // 1. CALCULATE GEOMETRY (Static)
    const geometries = useMemo(() => {
        if (!fullData || fullData.length === 0 || !realSectors) return null;

        const s1_limit = realSectors.s1_end;
        const s2_limit = realSectors.s2_end;

        const idx_s1 = fullData.findIndex(d => d.Distance > s1_limit);
        const idx_s2 = fullData.findIndex(d => d.Distance > s2_limit);

        const s1Data = fullData.slice(0, idx_s1 + 1);
        const s2Data = fullData.slice(idx_s1 - 1, idx_s2 + 1);
        const s3Data = [...fullData.slice(idx_s2 - 1), fullData[0]];
        const fullLoop = [...fullData, fullData[0]];

        return {
            s1: { x: s1Data.map(d => d.X), y: s1Data.map(d => d.Y) },
            s2: { x: s2Data.map(d => d.X), y: s2Data.map(d => d.Y) },
            s3: { x: s3Data.map(d => d.X), y: s3Data.map(d => d.Y) },
            full: { x: fullLoop.map(d => d.X), y: fullLoop.map(d => d.Y) }
        };
    }, [fullData, realSectors]);

    // 2. CONFIGURE SECTOR TRACES (Updates on distance change)
    const sectorTraces = useMemo(() => {
        if (!geometries || mapMode !== 'broadcast' || !realSectors) return [];

        // Blueprint Colors
        const s1_col = realSectors.colors.s1 === '#b124e8' ? '#a855f7' : (realSectors.colors.s1 === '#00ff00' ? '#16a34a' : '#ca8a04');
        const s2_col = realSectors.colors.s2 === '#b124e8' ? '#a855f7' : (realSectors.colors.s2 === '#00ff00' ? '#16a34a' : '#ca8a04');
        const s3_col = realSectors.colors.s3 === '#b124e8' ? '#a855f7' : (realSectors.colors.s3 === '#00ff00' ? '#16a34a' : '#ca8a04');

        const C_INACTIVE = '#cbd5e1';

        const colS1 = currentDistance > realSectors.s1_end ? s1_col : C_INACTIVE;
        const colS2 = currentDistance > realSectors.s2_end ? s2_col : C_INACTIVE;
        const colS3 = currentDistance > (realSectors.track_length - 200) ? s3_col : C_INACTIVE;

        const makeTrace = (geo, color, name) => ({
            x: geo.x, y: geo.y, mode: 'lines',
            line: { color: color, width: 8, shape: 'spline', smoothing: 1.3 },
            hoverinfo: 'none', type: 'scatter', name: name
        });

        return [
            makeTrace(geometries.s1, colS1, 'Sector 1'),
            makeTrace(geometries.s2, colS2, 'Sector 2'),
            makeTrace(geometries.s3, colS3, 'Sector 3')
        ];

    }, [geometries, currentDistance, mapMode, realSectors]);

    const borderTrace = useMemo(() => {
        if (!geometries) return null;
        return {
            x: geometries.full.x, y: geometries.full.y, mode: 'lines',
            line: { color: '#0f172a', width: 20, shape: 'spline', smoothing: 1.3 },
            hoverinfo: 'none', type: 'scatter', name: 'Border'
        };
    }, [geometries]);

    const fillTrace = useMemo(() => {
        if (!geometries) return null;
        return {
            x: geometries.full.x, y: geometries.full.y, mode: 'lines',
            line: { color: '#ffffff', width: 12, shape: 'spline', smoothing: 1.3 },
            hoverinfo: 'none', type: 'scatter', name: 'Fill'
        };
    }, [geometries]);

    const heatmapTrace = useMemo(() => {
        if (!fullData || mapMode !== 'engineering') return null;
        return {
            x: fullData.map(d => d.X), y: fullData.map(d => d.Y), mode: 'markers',
            marker: { color: fullData.map(d => d.Speed), colorscale: 'Viridis', size: 6 },
            hoverinfo: 'text', text: fullData.map(d => `${Math.round(d.Speed)} km/h`),
            type: 'scatter'
        };
    }, [fullData, mapMode]);

    if (!fullData || !fullData.length) return <div style={{color:'#94a3b8', textAlign:'center', marginTop:'40%', fontFamily:'Inter'}}>NO GPS DATA LOADED</div>;

    // --- UPDATED DRIVER TRACE (DOT, NO ROTATION) ---
    const driverTrace = {
        x: [driverPosition.x],
        y: [driverPosition.y],
        mode: 'markers',
        marker: {
            color: '#2563eb', // Blueprint Blue
            size: 16,         // Dot Size
            symbol: 'circle', // Fixed Circle
            line: { color: '#ffffff', width: 3 } // Thicker white stroke for contrast
        },
        type: 'scatter', name: 'Driver'
    };

    const anomalyTrace = {
        x: anomalies.map(i => fullData[i]?.X),
        y: anomalies.map(i => fullData[i]?.Y),
        mode: 'markers',
        marker: { color: '#dc2626', size: 14, symbol: 'x-thin', line: {width: 3, color: '#dc2626'} },
        type: 'scatter'
    };

    let layers = [];
    if (borderTrace) layers.push(borderTrace);
    if (fillTrace) layers.push(fillTrace);
    if (mapMode === 'broadcast') layers.push(...sectorTraces);
    else if (mapMode === 'engineering' && heatmapTrace) layers.push(heatmapTrace);
    layers.push(anomalyTrace);
    layers.push(driverTrace);

    return (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
            <Plot
                data={layers}
                layout={{
                    autosize: true,
                    margin: { t: 0, r: 0, l: 0, b: 0 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    xaxis: { visible: false, fixedrange: true, scaleanchor: 'y', scaleratio: 1 },
                    yaxis: { visible: false, fixedrange: true },
                    showlegend: false, hovermode: false
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                config={{ displayModeBar: false, staticPlot: false }}
            />
            <div style={{
                position: 'absolute', top: '24px', left: '24px', color: '#64748b',
                fontSize: '10px', fontWeight: '700', fontFamily: 'JetBrains Mono', letterSpacing: '1px',
                background: 'rgba(255,255,255,0.95)', padding: '6px 12px', borderRadius: '6px',
                border: '1px solid #e2e8f0', boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
            }}>
                {mapMode === 'broadcast' ? 'BROADCAST FEED' : 'TELEMETRY FEED'}
            </div>
        </div>
    );
};

export default TrackMap;