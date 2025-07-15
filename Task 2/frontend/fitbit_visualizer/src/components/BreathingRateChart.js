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

const SLEEP_COLORS = {
    deep_sleep_rate: '#1976d2',
    rem_sleep_rate: '#388e3c',
    light_sleep_rate: '#f57c00',
    full_sleep_rate: '#7b1fa2'
};

const SLEEP_LABELS = {
    deep_sleep_rate: 'Deep Sleep',
    rem_sleep_rate: 'REM Sleep',
    light_sleep_rate: 'Light Sleep',
    full_sleep_rate: 'Full Sleep'
};

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div style={{
                backgroundColor: '#fff',
                border: '1px solid #ccc',
                borderRadius: '5px',
                padding: '10px'
            }}>
                <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>{formatDate(label)}</p>
                {payload.map((entry, index) => (
                    <p key={index} style={{
                        margin: '2px 0',
                        color: entry.color,
                        fontSize: '12px'
                    }}>
                        {SLEEP_LABELS[entry.dataKey] || entry.dataKey}: {entry.value ? entry.value.toFixed(1) : 'N/A'} bpm
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

const BreathingRateChart = ({ data, loading, error }) => {
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
                <Typography variant="body1">No breathing rate data available for the selected period.</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ width: '100%', height: 400, mt: 3 }}>
            <ResponsiveContainer>
                <LineChart
                    data={data}
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
                        domain={[8, 25]}
                        tick={{ fontSize: 12 }}
                        label={{
                            value: 'Breathing Rate (bpm)',
                            angle: -90,
                            position: 'insideLeft',
                            style: { textAnchor: 'middle', fontSize: 12 }
                        }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />

                    <ReferenceLine
                        y={12}
                        stroke="#ff9800"
                        strokeDasharray="3 3"
                        label={{
                            value: "Normal Rest (12 bpm)",
                            position: 'insideTopRight',
                            fill: '#ff9800',
                            fontSize: 10
                        }}
                    />

                    <ReferenceLine
                        y={20}
                        stroke="#f44336"
                        strokeDasharray="3 3"
                        label={{
                            value: "Elevated (20 bpm)",
                            position: 'insideTopRight',
                            fill: '#f44336',
                            fontSize: 10
                        }}
                    />

                    <Line
                        name="Deep Sleep"
                        type="monotone"
                        dataKey="deep_sleep_rate"
                        stroke={SLEEP_COLORS.deep_sleep_rate}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                        strokeWidth={2}
                        connectNulls
                    />

                    <Line
                        name="REM Sleep"
                        type="monotone"
                        dataKey="rem_sleep_rate"
                        stroke={SLEEP_COLORS.rem_sleep_rate}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                        strokeWidth={2}
                        connectNulls
                    />

                    <Line
                        name="Light Sleep"
                        type="monotone"
                        dataKey="light_sleep_rate"
                        stroke={SLEEP_COLORS.light_sleep_rate}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                        strokeWidth={2}
                        connectNulls
                    />

                    <Line
                        name="Full Sleep"
                        type="monotone"
                        dataKey="full_sleep_rate"
                        stroke={SLEEP_COLORS.full_sleep_rate}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                        strokeWidth={2}
                        connectNulls
                    />

                    <Brush dataKey="timestamp" height={30} stroke="#8884d8" tickFormatter={formatDate} />
                </LineChart>
            </ResponsiveContainer>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: SLEEP_COLORS.deep_sleep_rate, borderRadius: '50%' }} />
                    <Typography variant="caption">Deep Sleep (Lowest)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: SLEEP_COLORS.rem_sleep_rate, borderRadius: '50%' }} />
                    <Typography variant="caption">REM Sleep (Variable)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: SLEEP_COLORS.light_sleep_rate, borderRadius: '50%' }} />
                    <Typography variant="caption">Light Sleep (Highest)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: SLEEP_COLORS.full_sleep_rate, borderRadius: '50%' }} />
                    <Typography variant="caption">Full Sleep (Average)</Typography>
                </Box>
            </Box>
        </Box>
    );
};

export default BreathingRateChart;