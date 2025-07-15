import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine, Brush, Area, ComposedChart
} from 'recharts';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString();
};

const calculateMovingAverage = (data, windowSize = 7) => {
    if (data.length < windowSize) return data;

    return data.map((item, index) => {
        const start = Math.max(0, index - Math.floor(windowSize / 2));
        const end = Math.min(data.length, start + windowSize);
        const window = data.slice(start, end);
        const avgSteps = window.reduce((sum, d) => sum + (d.steps || 0), 0) / window.length;

        return {
            ...item,
            movingAvgSteps: avgSteps
        };
    });
};

const getActivityLevel = (steps) => {
    if (steps >= 15000) return 'Very Active';
    if (steps >= 10000) return 'Active';
    if (steps >= 7500) return 'Somewhat Active';
    if (steps >= 5000) return 'Lightly Active';
    return 'Sedentary';
};

const getActivityColor = (steps) => {
    if (steps >= 15000) return '#4caf50';
    if (steps >= 10000) return '#8bc34a';
    if (steps >= 7500) return '#ffeb3b';
    if (steps >= 5000) return '#ff9800';
    return '#f44336';
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
                <p style={{ margin: '2px 0', color: '#2196f3', fontSize: '12px' }}>
                    Steps: {data.steps ? data.steps.toLocaleString() : 'N/A'}
                </p>
                <p style={{ margin: '2px 0', color: '#ff9800', fontSize: '12px' }}>
                    7-Day Avg: {data.movingAvgSteps ? data.movingAvgSteps.toLocaleString() : 'N/A'}
                </p>
                <p style={{ margin: '2px 0', color: getActivityColor(data.steps), fontSize: '12px' }}>
                    Level: {getActivityLevel(data.steps)}
                </p>
            </div>
        );
    }
    return null;
};

const ActivityLineChart = ({ data, loading, error }) => {
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
                <Typography variant="body1">No activity data available for the selected period.</Typography>
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
                        domain={[0, 'dataMax + 2000']}
                        tick={{ fontSize: 12 }}
                        label={{
                            value: 'Steps',
                            angle: -90,
                            position: 'insideLeft',
                            style: { textAnchor: 'middle', fontSize: 12 }
                        }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />

                    <ReferenceLine
                        y={10000}
                        stroke="#4caf50"
                        strokeDasharray="3 3"
                        label={{
                            value: "Daily Goal (10,000)",
                            position: 'insideTopRight',
                            fill: '#4caf50',
                            fontSize: 10
                        }}
                    />

                    <ReferenceLine
                        y={15000}
                        stroke="#2196f3"
                        strokeDasharray="3 3"
                        label={{
                            value: "Very Active (15,000)",
                            position: 'insideTopRight',
                            fill: '#2196f3',
                            fontSize: 10
                        }}
                    />

                    <Line
                        name="Daily Steps"
                        type="monotone"
                        dataKey="steps"
                        stroke="#2196f3"
                        dot={{ r: 4 }}
                        activeDot={{ r: 6 }}
                        strokeWidth={2}
                        connectNulls
                    />

                    <Line
                        name="7-Day Average"
                        type="monotone"
                        dataKey="movingAvgSteps"
                        stroke="#ff9800"
                        dot={false}
                        strokeDasharray="5 5"
                        strokeWidth={2}
                        connectNulls
                    />

                    <Brush dataKey="timestamp" height={30} stroke="#2196f3" tickFormatter={formatDate} />
                </LineChart>
            </ResponsiveContainer>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#4caf50', borderRadius: '50%' }} />
                    <Typography variant="caption">Very Active (≥15,000)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#8bc34a', borderRadius: '50%' }} />
                    <Typography variant="caption">Active (10,000-15,000)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#ffeb3b', borderRadius: '50%' }} />
                    <Typography variant="caption">Somewhat Active (7,500-10,000)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#ff9800', borderRadius: '50%' }} />
                    <Typography variant="caption">Lightly Active (5,000-7,500)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#f44336', borderRadius: '50%' }} />
                    <Typography variant="caption">Sedentary (&lt;5,000)</Typography>
                </Box>
            </Box>
        </Box>
    );
};

export default ActivityLineChart;