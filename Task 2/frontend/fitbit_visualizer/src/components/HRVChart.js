import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine, Brush
} from 'recharts';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString();
};

const getCoverageColor = (coverage) => {
    if (coverage >= 0.9) return '#4caf50';
    if (coverage >= 0.8) return '#ff9800';
    return '#f44336';
};

const calculateMovingAverage = (data, windowSize = 7) => {
    if (data.length < windowSize) return data;

    return data.map((item, index) => {
        const start = Math.max(0, index - Math.floor(windowSize / 2));
        const end = Math.min(data.length, start + windowSize);
        const window = data.slice(start, end);
        const avgRmssd = window.reduce((sum, d) => sum + (d.rmssd || 0), 0) / window.length;

        return {
            ...item,
            movingAvgRmssd: avgRmssd
        };
    });
};

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
            <div style={{
                backgroundColor: '#fff',
                border: '1px solid #ccc',
                borderRadius: '5px',
                padding: '10px'
            }}>
                <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>{formatDate(label)}</p>
                <p style={{ margin: '2px 0', color: '#8884d8', fontSize: '12px' }}>
                    RMSSD: {data.rmssd ? data.rmssd.toFixed(2) : 'N/A'} ms
                </p>
                <p style={{ margin: '2px 0', color: '#82ca9d', fontSize: '12px' }}>
                    7-Day Avg: {data.movingAvgRmssd ? data.movingAvgRmssd.toFixed(2) : 'N/A'} ms
                </p>
                <p style={{ margin: '2px 0', color: getCoverageColor(data.coverage), fontSize: '12px' }}>
                    Coverage: {data.coverage ? (data.coverage * 100).toFixed(1) : 'N/A'}%
                </p>
            </div>
        );
    }
    return null;
};

const HRVChart = ({ data, loading, error }) => {
    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ mb: 3 }}>
                {error}
            </Alert>
        );
    }

    if (!data || data.length === 0) {
        return (
            <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="body1">No HRV data available for the selected period.</Typography>
            </Box>
        );
    }

    const processedData = calculateMovingAverage(data);

    return (
        <Box sx={{ width: '100%', height: 400, mt: 3 }}>
            <ResponsiveContainer>
                <LineChart
                    data={processedData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                    <XAxis
                        dataKey="timestamp"
                        scale="time"
                        type="number"
                        domain={['auto', 'auto']}
                        tickFormatter={formatDate}
                        tick={{ fontSize: 12 }}
                    />
                    <YAxis
                        domain={['auto', 'auto']}
                        tick={{ fontSize: 12 }}
                        label={{
                            value: 'RMSSD (ms)',
                            angle: -90,
                            position: 'insideLeft',
                            style: { textAnchor: 'middle', fontSize: 12 }
                        }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />

                    <ReferenceLine
                        y={20}
                        stroke="#ff9800"
                        strokeDasharray="3 3"
                        label={{
                            value: "Low HRV",
                            position: 'insideTopRight',
                            fill: '#ff9800',
                            fontSize: 10
                        }}
                    />

                    <ReferenceLine
                        y={50}
                        stroke="#4caf50"
                        strokeDasharray="3 3"
                        label={{
                            value: "Good HRV",
                            position: 'insideTopRight',
                            fill: '#4caf50',
                            fontSize: 10
                        }}
                    />

                    <Line
                        name="RMSSD"
                        type="monotone"
                        dataKey="rmssd"
                        stroke="#8884d8"
                        dot={{ r: 4 }}
                        activeDot={{ r: 6 }}
                        strokeWidth={2}
                        connectNulls
                    />

                    <Line
                        name="7-Day Moving Average"
                        type="monotone"
                        dataKey="movingAvgRmssd"
                        stroke="#82ca9d"
                        dot={false}
                        strokeDasharray="5 5"
                        strokeWidth={2}
                        connectNulls
                    />

                    <Brush dataKey="timestamp" height={30} stroke="#8884d8" tickFormatter={formatDate} />
                </LineChart>
            </ResponsiveContainer>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#4caf50', borderRadius: '50%' }} />
                    <Typography variant="caption">Good Coverage (≥90%)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#ff9800', borderRadius: '50%' }} />
                    <Typography variant="caption">Fair Coverage (80-90%)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#f44336', borderRadius: '50%' }} />
                    <Typography variant="caption">Poor Coverage (&lt;80%)</Typography>
                </Box>
            </Box>
        </Box>
    );
};

export default HRVChart;