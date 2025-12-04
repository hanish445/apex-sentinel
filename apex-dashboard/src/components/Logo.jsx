import React from 'react';

const Logo = ({ width = 40, height = 40 }) => (
    <svg
        width={width}
        height={height}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Apex Sentinel Logo"
    >
        {/* Construction Lines (The "Blueprint" look) */}
        <line x1="50" y1="5" x2="50" y2="95" stroke="#cbd5e1" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="10" y1="50" x2="90" y2="50" stroke="#cbd5e1" strokeWidth="1" strokeDasharray="4 4" />

        {/* Shield Base - Technical Outline */}
        <path
            d="M50 10 L85 25 V50 C85 70 50 90 50 90 C50 90 15 70 15 50 V25 L50 10 Z"
            stroke="#2563eb"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="rgba(37, 99, 235, 0.05)"
        />

        {/* Apex Trajectory Line */}
        <path
            d="M32 65 L50 38 L80 38"
            stroke="#dc2626"
            strokeWidth="4"
            strokeLinecap="square"
        />

        {/* Sensor Nodes */}
        <circle cx="32" cy="65" r="3" fill="#ffffff" stroke="#dc2626" strokeWidth="2" />
        <circle cx="50" cy="10" r="2" fill="#2563eb" />
        <circle cx="50" cy="90" r="2" fill="#2563eb" />

        {/* Technical Markings */}
        <path d="M42 78 H58" stroke="#0f172a" strokeWidth="2" />
        <path d="M45 84 H55" stroke="#0f172a" strokeWidth="1" />
    </svg>
);

export default Logo;