import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

const TrackMap = ({ fullData, currentIndex, anomalies }) => {
    const trackTrace = useMemo(() => {
        if (!fullData || fullData.length === 0) return null;
        return {
            x: fullData.map(d => d.X),
            y: fullData.map(d => d.Y),
            mode: 'lines',
            line: { color: '#27272a', width: 4 }, // Dark grey path
            hoverinfo: 'none',
            type: 'scatter'
        };
    }, [fullData]);

    const driverTrace = {
        x: [fullData[currentIndex]?.X],
        y: [fullData[currentIndex]?.Y],
        mode: 'markers',
        marker: { color: '#3b82f6', size: 10, symbol: 'circle' }, // Blue dot
        name: 'Driver',
        type: 'scatter'
    };

    const anomalyTrace = {
        x: anomalies.map(idx => fullData[idx]?.X),
        y: anomalies.map(idx => fullData[idx]?.Y),
        mode: 'markers',
        marker: { color: '#ef4444', size: 8, symbol: 'x' }, // Red X
        name: 'Anomaly',
        type: 'scatter'
    };

    const layout = {
        autosize: true,
        margin: { t: 0, r: 0, l: 0, b: 0 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: { showgrid: false, zeroline: false, showticklabels: false, visible: false },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false, visible: false, scaleanchor: 'x' },
        showlegend: false,
        dragmode: false
    };

    return (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
            <Plot
                data={[trackTrace, anomalyTrace, driverTrace]}
                layout={layout}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                config={{ displayModeBar: false }}
            />
            <div style={{
                position: 'absolute', top: '10px', left: '10px',
                color: '#52525b', fontSize: '10px', fontWeight: 'bold', fontFamily: 'JetBrains Mono'
            }}>
                LIVE GPS TRACKING
            </div>
        </div>
    );
};

export default TrackMap;