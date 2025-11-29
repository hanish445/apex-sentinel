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
        {/* Shield Base */}
        <path
            d="M50 5 L90 20 V50 C90 75 50 95 50 95 C50 95 10 75 10 50 V20 L50 5 Z"
            stroke="white"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
        />

        {/* Apex Speed Line */}
        <path
            d="M30 65 L50 35 L85 35"
            stroke="#e10600"
            strokeWidth="6"
            strokeLinecap="square"
        />

        {/* Sensor Dot */}
        <circle cx="30" cy="65" r="4" fill="#e10600" />

        {/* Tech Details */}
        <path d="M40 75 H60" stroke="#3f3f46" strokeWidth="2" />
        <path d="M45 82 H55" stroke="#3f3f46" strokeWidth="2" />
    </svg>
);

export default Logo;