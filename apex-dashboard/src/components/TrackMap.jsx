import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

const TrackMap = ({ fullData, currentIndex, anomalies, mapMode, realSectors }) => {

    // 1. CALCULATE GEOMETRY ONCE (Heavy calculation, only runs on load)
    const sectorGeometry = useMemo(() => {
        if (!fullData || fullData.length === 0 || !realSectors) return null;

        const s1_limit = realSectors.s1_end;
        const s2_limit = realSectors.s2_end;

        // Split data into static arrays
        const dataS1 = fullData.filter(d => d.Distance <= s1_limit);
        const dataS2 = fullData.filter(d => d.Distance > s1_limit && d.Distance <= s2_limit);
        const dataS3 = fullData.filter(d => d.Distance > s2_limit);

        return {
            s1: { x: dataS1.map(d => d.X), y: dataS1.map(d => d.Y) },
            s2: { x: dataS2.map(d => d.X), y: dataS2.map(d => d.Y) },
            s3: { x: dataS3.map(d => d.X), y: dataS3.map(d => d.Y) }
        };
    }, [fullData, realSectors]); // Dependencies ensure this DOES NOT run on currentIndex change

    // 2. APPLY COLORS (Light calculation, runs every tick)
    const sectorTraces = useMemo(() => {
        if (!sectorGeometry || mapMode !== 'broadcast' || !realSectors) return [];

        const currentDist = fullData[currentIndex]?.Distance || 0;

        // Colors from backend
        const colors = realSectors.colors || { s1: '#b124e8', s2: '#00ff00', s3: '#fff200' };
        const C_WHITE = '#ffffff';

        // Fast state check
        const colS1 = currentDist > realSectors.s1_end ? colors.s1 : C_WHITE;
        const colS2 = currentDist > realSectors.s2_end ? colors.s2 : C_WHITE;
        const colS3 = currentDist > (realSectors.track_length - 200) ? colors.s3 : C_WHITE;

        const makeTrace = (geo, color, name) => ({
            x: geo.x,
            y: geo.y,
            mode: 'lines',
            line: { color: color, width: 8 },
            hoverinfo: 'none',
            type: 'scatter',
            name: name
        });

        return [
            makeTrace(sectorGeometry.s1, colS1, 'Sector 1'),
            makeTrace(sectorGeometry.s2, colS2, 'Sector 2'),
            makeTrace(sectorGeometry.s3, colS3, 'Sector 3')
        ];

    }, [sectorGeometry, currentIndex, mapMode, realSectors, fullData]); // Colors update on tick

    // 3. BASE TRACK (Memoized)
    const borderTrace = useMemo(() => {
        if (!fullData || !fullData.length) return null;
        return {
            x: fullData.map(d => d.X),
            y: fullData.map(d => d.Y),
            mode: 'lines',
            line: { color: '#000000', width: 16 }, // Black Border
            hoverinfo: 'none',
            type: 'scatter',
            name: 'Border'
        };
    }, [fullData]);

    // 4. HEATMAP (Engineering Mode)
    const heatmapTrace = useMemo(() => {
        if (!fullData || mapMode !== 'engineering') return null;
        return {
            x: fullData.map(d => d.X),
            y: fullData.map(d => d.Y),
            mode: 'markers',
            marker: {
                color: fullData.map(d => d.Speed),
                colorscale: 'Viridis',
                size: 6,
            },
            hoverinfo: 'text',
            text: fullData.map(d => `${Math.round(d.Speed)} km/h`),
            type: 'scatter'
        };
    }, [fullData, mapMode]);

    if (!fullData || !fullData.length) return <div style={{color:'#666'}}>NO GPS DATA</div>;

    // Driver Marker Calculation
    const curr = fullData[currentIndex] || fullData[0];
    const next = fullData[Math.min(currentIndex + 5, fullData.length - 1)] || curr;
    let angle = Math.atan2(next.Y - curr.Y, next.X - curr.X) * (180 / Math.PI);
    angle = angle - 90;

    const driverTrace = {
        x: [curr.X], y: [curr.Y],
        mode: 'markers',
        marker: {
            color: '#fff200', size: 14, symbol: 'triangle-up',
            angle: angle, line: { color: '#000', width: 2 }
        },
        type: 'scatter', name: 'Driver'
    };

    const anomalyTrace = {
        x: anomalies.map(i => fullData[i]?.X),
        y: anomalies.map(i => fullData[i]?.Y),
        mode: 'markers',
        marker: { color: '#e10600', size: 10, symbol: 'x' },
        type: 'scatter'
    };

    // Layer Assembly
    let layers = [];
    if (borderTrace) layers.push(borderTrace);

    if (mapMode === 'broadcast') {
        layers.push(...sectorTraces);
    } else if (mapMode === 'engineering' && heatmapTrace) {
        layers.push(heatmapTrace);
    } else {
        if (borderTrace) layers.push({...borderTrace, line: {color: '#fff', width: 8}});
    }

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
                    xaxis: { visible: false, fixedrange: true },
                    yaxis: { visible: false, scaleanchor: 'x', fixedrange: true },
                    showlegend: false,
                    hovermode: false
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                config={{ displayModeBar: false, staticPlot: false }}
            />
            <div style={{
                position: 'absolute', top: '15px', left: '15px',
                color: mapMode === 'broadcast' ? '#a855f7' : '#00ff00',
                fontSize: '10px', fontWeight: 'bold', fontFamily: 'JetBrains Mono', letterSpacing: '1px',
                background: 'rgba(0,0,0,0.6)', padding: '4px 8px', borderRadius: '4px', border: '1px solid #333'
            }}>
                {mapMode === 'broadcast' ? 'BROADCAST FEED (SECTOR PERF)' : 'ENGINEERING TELEMETRY'}
            </div>
        </div>
    );
};

export default TrackMap;