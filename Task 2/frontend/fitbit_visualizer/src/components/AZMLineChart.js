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

const AZM_COLORS = {
    total_azm: '#9c27b0',
    fat_burn: '#ffb74d',
    cardio: '#64b5f6',
    peak: '#e57373'
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
                        {entry.name}: {entry.value ? entry.value.toFixed(2) : '0.00'} min
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

const AZMLineChart = ({ data, loading, error }) => {
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
                <Typography variant="body1">No Active Zone Minutes data available for the selected period.</Typography>
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
                        tick={{ fontSize: 12 }}
                        label={{
                            value: 'Minutes',
                            angle: -90,
                            position: 'insideLeft',
                            style: { textAnchor: 'middle', fontSize: 12 }
                        }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />

                    <ReferenceLine
                        y={0.5}
                        stroke="#ff9800"
                        strokeDasharray="3 3"
                        label={{
                            value: "Low Activity",
                            position: 'insideTopRight',
                            fill: '#ff9800',
                            fontSize: 10
                        }}
                    />

                    <Line
                        name="Total AZM"
                        type="monotone"
                        dataKey="total_azm"
                        stroke={AZM_COLORS.total_azm}
                        strokeWidth={3}
                        dot={{ r: 5 }}
                        activeDot={{ r: 7 }}
                        connectNulls
                    />

                    <Line
                        name="Fat Burn"
                        type="monotone"
                        dataKey="fat_burn"
                        stroke={AZM_COLORS.fat_burn}
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                        connectNulls
                    />

                    <Line
                        name="Cardio"
                        type="monotone"
                        dataKey="cardio"
                        stroke={AZM_COLORS.cardio}
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                        connectNulls
                    />

                    <Line
                        name="Peak"
                        type="monotone"
                        dataKey="peak"
                        stroke={AZM_COLORS.peak}
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                        connectNulls
                    />

                    <Brush dataKey="timestamp" height={30} stroke="#9c27b0" tickFormatter={formatDate} />
                </LineChart>
            </ResponsiveContainer>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: AZM_COLORS.total_azm, borderRadius: '50%' }} />
                    <Typography variant="caption">Total AZM</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: AZM_COLORS.fat_burn, borderRadius: '50%' }} />
                    <Typography variant="caption">Fat Burn</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: AZM_COLORS.cardio, borderRadius: '50%' }} />
                    <Typography variant="caption">Cardio</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: AZM_COLORS.peak, borderRadius: '50%' }} />
                    <Typography variant="caption">Peak</Typography>
                </Box>
            </Box>
        </Box>
    );
};

export default AZMLineChart;