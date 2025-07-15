import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

const ZONE_COLORS = {
    'Out of Range': '#bdbdbd',
    'Fat Burn': '#ffb74d',
    'Cardio': '#64b5f6',
    'Peak': '#e57373'
};

const processZoneData = (data) => {
    const grouped = {};
    data.forEach(item => {
        const day = item.timestamp.split('T')[0];
        if (!grouped[day]) {
            grouped[day] = { day };
        }
        grouped[day][item.zone_name] = Math.round(item.minutes / 60 * 10) / 10;
    });
    return Object.values(grouped).sort((a, b) => new Date(a.day) - new Date(b.day));
};

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div style={{
                backgroundColor: '#fff',
                border: '1px solid #ccc',
                padding: '10px',
                borderRadius: '5px'
            }}>
                <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>{label}</p>
                {payload.map((entry, index) => (
                    <p key={index} style={{
                        margin: '2px 0',
                        color: entry.color,
                        fontSize: '12px'
                    }}>
                        {entry.name}: {entry.value || 0} hours
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

const HeartRateZoneChart = ({ data, loading, error }) => {
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
                <Typography variant="body1">No heart rate zone data available for the selected period.</Typography>
            </Box>
        );
    }

    const processedData = processZoneData(data);
    const zoneKeys = ['Out of Range', 'Fat Burn', 'Cardio', 'Peak'];

    return (
        <Box sx={{ width: '100%', height: 400, mt: 3 }}>
            <ResponsiveContainer>
                <BarChart
                    data={processedData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                    <XAxis
                        dataKey="day"
                        tick={{ fontSize: 12 }}
                        angle={-45}
                        textAnchor="end"
                        height={60}
                    />
                    <YAxis
                        tick={{ fontSize: 12 }}
                        label={{
                            value: 'Hours',
                            angle: -90,
                            position: 'insideLeft',
                            style: { textAnchor: 'middle' }
                        }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    {zoneKeys.map(zone => (
                        <Bar
                            key={zone}
                            dataKey={zone}
                            stackId="zones"
                            fill={ZONE_COLORS[zone]}
                            name={zone}
                        />
                    ))}
                </BarChart>
            </ResponsiveContainer>
        </Box>
    );
};

export default HeartRateZoneChart;