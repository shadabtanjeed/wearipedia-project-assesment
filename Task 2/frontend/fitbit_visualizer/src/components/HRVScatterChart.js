import React from 'react';
import {
    ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

const getCoverageColor = (coverage) => {
    if (coverage >= 0.9) return '#4caf50';
    if (coverage >= 0.8) return '#ff9800';
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
                <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>
                    {new Date(data.timestamp).toLocaleDateString()}
                </p>
                <p style={{ margin: '2px 0', fontSize: '12px' }}>
                    HF: {data.hf ? data.hf.toFixed(2) : 'N/A'} ms²
                </p>
                <p style={{ margin: '2px 0', fontSize: '12px' }}>
                    LF: {data.lf ? data.lf.toFixed(2) : 'N/A'} ms²
                </p>
                <p style={{ margin: '2px 0', fontSize: '12px' }}>
                    LF/HF Ratio: {data.hf && data.lf ? (data.lf / data.hf).toFixed(2) : 'N/A'}
                </p>
                <p style={{ margin: '2px 0', color: getCoverageColor(data.coverage), fontSize: '12px' }}>
                    Coverage: {data.coverage ? (data.coverage * 100).toFixed(1) : 'N/A'}%
                </p>
            </div>
        );
    }
    return null;
};

const HRVScatterChart = ({ data, loading, error }) => {
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

    const scatterData = data.map(item => ({
        ...item,
        x: item.lf || 0,
        y: item.hf || 0,
        fill: getCoverageColor(item.coverage || 0)
    }));

    return (
        <Box sx={{ width: '100%', height: 400, mt: 3 }}>
            <ResponsiveContainer>
                <ScatterChart
                    data={scatterData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                    <XAxis
                        dataKey="x"
                        type="number"
                        domain={['auto', 'auto']}
                        tick={{ fontSize: 12 }}
                        label={{
                            value: 'LF Power (ms²)',
                            position: 'insideBottom',
                            offset: -5,
                            style: { textAnchor: 'middle', fontSize: 12 }
                        }}
                    />
                    <YAxis
                        dataKey="y"
                        type="number"
                        domain={['auto', 'auto']}
                        tick={{ fontSize: 12 }}
                        label={{
                            value: 'HF Power (ms²)',
                            angle: -90,
                            position: 'insideLeft',
                            style: { textAnchor: 'middle', fontSize: 12 }
                        }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />

                    <ReferenceLine
                        x={200}
                        stroke="#ff9800"
                        strokeDasharray="3 3"
                        label={{
                            value: "LF Threshold",
                            position: 'insideTopRight',
                            fill: '#ff9800',
                            fontSize: 10
                        }}
                    />

                    <ReferenceLine
                        y={400}
                        stroke="#4caf50"
                        strokeDasharray="3 3"
                        label={{
                            value: "HF Threshold",
                            position: 'insideTopRight',
                            fill: '#4caf50',
                            fontSize: 10
                        }}
                    />

                    <Scatter
                        name="HF vs LF Power"
                        data={scatterData}
                        fill="#8884d8"
                    />
                </ScatterChart>
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

export default HRVScatterChart;