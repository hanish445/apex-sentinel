import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

const TrackMap = ({ fullData, currentIndex, anomalies }) => {
    const trackTrace = useMemo(() => {
        if (!fullData || fullData.length === 0) return null;
        if (fullData[0].X === undefined || fullData[0].Y === undefined) return null;

        return {
            x: fullData.map(d => d.X),
            y: fullData.map(d => d.Y),
            mode: 'lines',
            line: { color: '#333', width: 6 }, // Thicker, dark grey track
            hoverinfo: 'none',
            type: 'scatter',
            name: 'Circuit'
        };
    }, [fullData]);

    if (!fullData || !fullData.length || !trackTrace) {
        return (
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#4b5563', fontSize: '14px', fontFamily: 'Rajdhani', letterSpacing: '2px'}}>
                AWAITING GPS SIGNAL
            </div>
        );
    }

    const driverTrace = {
        x: [fullData[currentIndex]?.X],
        y: [fullData[currentIndex]?.Y],
        mode: 'markers',
        marker: {
            color: '#fff200', // Safety Yellow
            size: 16,
            symbol: 'circle',
            line: { color: '#000', width: 2 }
        },
        name: 'Driver',
        type: 'scatter',
        hoverinfo: 'skip'
    };

    const anomalyTrace = {
        x: anomalies.map(idx => fullData[idx]?.X),
        y: anomalies.map(idx => fullData[idx]?.Y),
        mode: 'markers',
        marker: { color: '#e10600', size: 10, symbol: 'x' }, // F1 Red
        name: 'Anomaly',
        type: 'scatter',
        hoverinfo: 'none'
    };

    const layout = {
        autosize: true,
        margin: { t: 20, r: 20, l: 20, b: 20 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: { showgrid: false, zeroline: false, showticklabels: false, visible: false, fixedrange: true },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false, visible: false, scaleanchor: 'x', fixedrange: true },
        showlegend: false,
        dragmode: false,
        hovermode: false
    };

    return (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
            <Plot
                data={[trackTrace, anomalyTrace, driverTrace]}
                layout={layout}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                config={{ displayModeBar: false, staticPlot: false }}
            />
            <div style={{
                position: 'absolute', top: '20px', left: '20px',
                color: '#00d2be', fontSize: '12px', fontWeight: 'bold', fontFamily: 'JetBrains Mono', letterSpacing: '1px'
            }}>
                LIVE GPS
            </div>
        </div>
    );
};

export default TrackMap;