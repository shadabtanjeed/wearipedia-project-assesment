import React from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell
} from 'recharts';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const getActivityColor = (steps) => {
    if (steps >= 15000) return '#4caf50';
    if (steps >= 10000) return '#8bc34a';
    if (steps >= 7500) return '#ffeb3b';
    if (steps >= 5000) return '#ff9800';
    return '#f44336';
};

const getActivityLevel = (steps) => {
    if (steps >= 15000) return 'Very Active';
    if (steps >= 10000) return 'Active';
    if (steps >= 7500) return 'Somewhat Active';
    if (steps >= 5000) return 'Lightly Active';
    return 'Sedentary';
};

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const steps = payload[0].value;
        return (
            <div style={{
                backgroundColor: '#fff',
                border: '1px solid #ccc',
                borderRadius: '5px',
                padding: '10px'
            }}>
                <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>{formatDate(label)}</p>
                <p style={{ margin: '2px 0', color: payload[0].color, fontSize: '12px' }}>
                    Steps: {steps ? steps.toLocaleString() : 'N/A'}
                </p>
                <p style={{ margin: '2px 0', color: getActivityColor(steps), fontSize: '12px' }}>
                    Level: {getActivityLevel(steps)}
                </p>
            </div>
        );
    }
    return null;
};

const ActivityBarChart = ({ data, loading, error }) => {
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

    return (
        <Box sx={{ width: '100%', height: 400, mt: 3 }}>
            <ResponsiveContainer>
                <BarChart
                    data={data}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                    <XAxis
                        dataKey="timestamp"
                        tickFormatter={formatDate}
                        tick={{ fontSize: 12 }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
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
                            value: "Daily Goal",
                            position: 'insideTopRight',
                            fill: '#4caf50',
                            fontSize: 10
                        }}
                    />

                    <Bar
                        name="Daily Steps"
                        dataKey="steps"
                        radius={[4, 4, 0, 0]}
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={getActivityColor(entry.steps)} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#4caf50' }} />
                    <Typography variant="caption">Very Active (≥15,000)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#8bc34a' }} />
                    <Typography variant="caption">Active (10,000-15,000)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#ffeb3b' }} />
                    <Typography variant="caption">Somewhat Active (7,500-10,000)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#ff9800' }} />
                    <Typography variant="caption">Lightly Active (5,000-7,500)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#f44336' }} />
                    <Typography variant="caption">Sedentary (&lt;5,000)</Typography>
                </Box>
            </Box>
        </Box>
    );
};

export default ActivityBarChart;