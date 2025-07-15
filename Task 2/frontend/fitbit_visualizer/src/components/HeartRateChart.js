import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, Brush, ReferenceLine
} from 'recharts';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString();
};

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div style={{
                backgroundColor: '#fff',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '5px'
            }}>
                <p style={{ margin: '0', fontWeight: 'bold' }}>{formatDate(label)}</p>
                {payload.map((entry, index) => (
                    entry.value !== null && entry.value !== undefined && (
                        <p key={index} style={{
                            margin: '5px 0',
                            color: entry.color
                        }}>
                            {entry.name}: {entry.value} bpm
                        </p>
                    )
                ))}
            </div>
        );
    }
    return null;
};

const HeartRateChart = ({ data, loading, error }) => {
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
                <Typography variant="body1">No heart rate data available for the selected period.</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ width: '100%', height: 400, mt: 3 }}>
            <ResponsiveContainer>
                <LineChart
                    data={data}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
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
                        domain={['dataMin - 10', 'dataMax + 10']}
                        tick={{ fontSize: 12 }}
                        label={{
                            value: 'Heart Rate (bpm)',
                            angle: -90,
                            position: 'insideLeft',
                            style: { textAnchor: 'middle', fontSize: 12 }
                        }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <ReferenceLine y={60} stroke="#ff7300" strokeDasharray="3 3" label={{ value: "Rest HR", position: 'insideBottomLeft', fill: '#ff7300', fontSize: 10 }} />
                    <ReferenceLine y={100} stroke="#ff0000" strokeDasharray="3 3" label={{ value: "Active HR", position: 'insideTopLeft', fill: '#ff0000', fontSize: 10 }} />
                    <Line
                        name="Heart Rate"
                        type="monotone"
                        dataKey="value"
                        stroke="#8884d8"
                        dot={false}
                        activeDot={{ r: 6 }}
                        strokeWidth={2}
                        connectNulls
                    />
                    <Line
                        name="Resting Heart Rate"
                        type="monotone"
                        dataKey="resting_heart_rate"
                        stroke="#82ca9d"
                        dot={false}
                        strokeDasharray="3 3"
                        strokeWidth={1.5}
                        connectNulls
                    />
                    <Brush dataKey="timestamp" height={30} stroke="#8884d8" tickFormatter={formatDate} />
                </LineChart>
            </ResponsiveContainer>
        </Box>
    );
};

export default HeartRateChart;