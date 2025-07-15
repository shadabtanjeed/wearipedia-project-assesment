import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine, ReferenceArea
} from 'recharts';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString();
};

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const value = payload[0].value;
        const status = value >= 95 ? 'Normal' : 'Below Normal';
        const statusColor = value >= 95 ? '#4caf50' : '#f44336';

        return (
            <div style={{
                backgroundColor: '#fff',
                border: '1px solid #ccc',
                borderRadius: '5px',
                padding: '20px'
            }}>
                <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>{formatDate(label)}</p>
                <p style={{
                    margin: '2px 0',
                    color: payload[0].color,
                    fontSize: '12px'
                }}>
                    SpO2: {value !== null ? value.toFixed(1) : 'N/A'}%
                </p>
                <p style={{
                    margin: '2px 0',
                    color: statusColor,
                    fontSize: '11px',
                    fontWeight: 'bold'
                }}>
                    Status: {status}
                </p>
            </div>
        );
    }
    return null;
};

const SpO2Chart = ({ data, loading, error }) => {
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
                <Typography variant="body1">No SpO2 data available for the selected period.</Typography>
            </Box>
        );
    }

    const minTimestamp = Math.min(...data.map(d => d.timestamp));
    const maxTimestamp = Math.max(...data.map(d => d.timestamp));

    return (
        <Box sx={{ width: '100%', height: 400, mt: 3 }}>
            <ResponsiveContainer>
                <LineChart
                    data={data}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} />

                    <ReferenceArea
                        y1={95}
                        y2={100}
                        fill="#e8f5e8"
                        fillOpacity={0.3}
                        stroke="none"
                    />

                    <ReferenceArea
                        y1={90}
                        y2={95}
                        fill="#fff3e0"
                        fillOpacity={0.3}
                        stroke="none"
                    />

                    <ReferenceArea
                        y1={85}
                        y2={90}
                        fill="#ffebee"
                        fillOpacity={0.3}
                        stroke="none"
                    />

                    <XAxis
                        dataKey="timestamp"
                        scale="time"
                        type="number"
                        domain={['auto', 'auto']}
                        tickFormatter={formatDate}
                        tick={{ fontSize: 12 }}
                    />

                    <YAxis
                        domain={[85, 100]}
                        tick={{ fontSize: 12 }}
                        label={{
                            value: 'SpO2 (%)',
                            angle: -90,
                            position: 'insideLeft',
                            style: { textAnchor: 'middle', fontSize: 12 }
                        }}
                    />

                    <Tooltip content={<CustomTooltip />} />
                    <Legend />

                    <ReferenceLine
                        y={95}
                        stroke="#4caf50"
                        strokeDasharray="3 3"
                        label={{
                            value: "Normal Threshold (95%)",
                            position: 'insideTopRight',
                            fill: '#4caf50',
                            fontSize: 10
                        }}
                    />

                    <ReferenceLine
                        y={90}
                        stroke="#ff9800"
                        strokeDasharray="3 3"
                        label={{
                            value: "Low (90%)",
                            position: 'insideTopRight',
                            fill: '#ff9800',
                            fontSize: 10
                        }}
                    />

                    <Line
                        name="Daily Average SpO2"
                        type="monotone"
                        dataKey="value"
                        stroke="#2196f3"
                        dot={{ r: 4, fill: '#2196f3' }}
                        activeDot={{ r: 6, fill: '#1976d2' }}
                        strokeWidth={2}
                        connectNulls
                    />
                </LineChart>
            </ResponsiveContainer>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#e8f5e8', border: '1px solid #4caf50' }} />
                    <Typography variant="caption">Normal (95-100%)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#fff3e0', border: '1px solid #ff9800' }} />
                    <Typography variant="caption">Low (90-95%)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: '#ffebee', border: '1px solid #f44336' }} />
                    <Typography variant="caption">Critical (&lt;90%)</Typography>
                </Box>
            </Box>
        </Box>
    );
};

export default SpO2Chart;