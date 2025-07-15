import React from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const AZM_COLORS = {
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

const AZMStackedChart = ({ data, loading, error }) => {
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

                    <Bar
                        name="Fat Burn"
                        dataKey="fat_burn"
                        stackId="azm"
                        fill={AZM_COLORS.fat_burn}
                        radius={[0, 0, 0, 0]}
                    />

                    <Bar
                        name="Cardio"
                        dataKey="cardio"
                        stackId="azm"
                        fill={AZM_COLORS.cardio}
                        radius={[0, 0, 0, 0]}
                    />

                    <Bar
                        name="Peak"
                        dataKey="peak"
                        stackId="azm"
                        fill={AZM_COLORS.peak}
                        radius={[2, 2, 0, 0]}
                    />
                </BarChart>
            </ResponsiveContainer>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: AZM_COLORS.fat_burn }} />
                    <Typography variant="caption">Fat Burn Zone</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: AZM_COLORS.cardio }} />
                    <Typography variant="caption">Cardio Zone</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 16, height: 16, backgroundColor: AZM_COLORS.peak }} />
                    <Typography variant="caption">Peak Zone</Typography>
                </Box>
            </Box>
        </Box>
    );
};

export default AZMStackedChart;