import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Paper, CircularProgress, Alert, Button } from '@mui/material';
import UserSelector from './components/UserSelector';
import DateRangePicker from './components/DateRangePicker';
import HeartRateChart from './components/HeartRateChart';
import HeartRateZoneChart from './components/HeartRateZoneChart';
import SpO2Chart from './components/SpO2Chart';
import { API_URL } from './services/api';
import { fetchUsers } from './services/users_api';
import { fetchDailyAvgHeartRateData, fetchHeartRateZonesData } from './services/heartRate_api';
import { fetchDailyAvgSpO2Data } from './services/spo2_api';
import './App.css';

function App() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-01-31');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [heartRateData, setHeartRateData] = useState([]);
  const [heartRateLoading, setHeartRateLoading] = useState(false);
  const [heartRateError, setHeartRateError] = useState(null);

  const [zoneData, setZoneData] = useState([]);
  const [zoneLoading, setZoneLoading] = useState(false);
  const [zoneError, setZoneError] = useState(null);

  const [spo2Data, setSpo2Data] = useState([]);
  const [spo2Loading, setSpo2Loading] = useState(false);
  const [spo2Error, setSpo2Error] = useState(null);

  const [showAllVisualizations, setShowAllVisualizations] = useState(false);
  const [visualizationLoading, setVisualizationLoading] = useState(false);

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const response = await fetchUsers();
        if (response.success) {
          setUsers(response.data || []);
          if (response.data && response.data.length > 0) {
            setSelectedUser(response.data[0].user_id);
          }
        } else {
          setError('Failed to fetch users: API returned unsuccessful response');
        }
      } catch (err) {
        setError('Failed to connect to the API server');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadUsers();
  }, []);

  const handleVisualizeAll = async () => {
    if (!selectedUser) {
      setHeartRateError("Please select a user");
      setZoneError("Please select a user");
      setSpo2Error("Please select a user");
      return;
    }

    setVisualizationLoading(true);
    setShowAllVisualizations(true);

    await Promise.all([
      fetchHeartRateData(),
      fetchZoneData(),
      fetchSpO2Data()
    ]);

    setVisualizationLoading(false);
  };

  const fetchHeartRateData = async () => {
    setHeartRateLoading(true);
    setHeartRateError(null);

    try {
      const response = await fetchDailyAvgHeartRateData(selectedUser, startDate, endDate);

      if (response.success) {
        const processedData = response.data.map(item => ({
          timestamp: new Date(item.day).getTime(),
          value: item.avg_heart_rate,
          resting_heart_rate: item.avg_resting_heart_rate
        })).sort((a, b) => a.timestamp - b.timestamp);

        setHeartRateData(processedData);

        if (response.warning) {
          setHeartRateError(response.warning);
        } else {
          setHeartRateError(null);
        }
      } else {
        setHeartRateError('Failed to fetch heart rate data');
      }
    } catch (err) {
      setHeartRateError(`Error fetching heart rate data: ${err.message}`);
      console.error(err);
    } finally {
      setHeartRateLoading(false);
    }
  };

  const fetchZoneData = async () => {
    setZoneLoading(true);
    setZoneError(null);

    try {
      const response = await fetchHeartRateZonesData(selectedUser, startDate, endDate);

      if (response.success) {
        setZoneData(response.data || []);
        if (response.warning) {
          setZoneError(response.warning);
        } else {
          setZoneError(null);
        }
      } else {
        setZoneError('Failed to fetch heart rate zone data');
      }
    } catch (err) {
      setZoneError(`Error fetching heart rate zone data: ${err.message}`);
      console.error(err);
    } finally {
      setZoneLoading(false);
    }
  };

  const fetchSpO2Data = async () => {
    setSpo2Loading(true);
    setSpo2Error(null);

    try {
      const response = await fetchDailyAvgSpO2Data(selectedUser, startDate, endDate);

      if (response.success) {
        const processedData = response.data.map(item => ({
          timestamp: new Date(item.day).getTime(),
          value: item.avg_spo2
        })).sort((a, b) => a.timestamp - b.timestamp);

        setSpo2Data(processedData);

        if (response.warning) {
          setSpo2Error(response.warning);
        } else {
          setSpo2Error(null);
        }
      } else {
        setSpo2Error('Failed to fetch SpO2 data');
      }
    } catch (err) {
      setSpo2Error(`Error fetching SpO2 data: ${err.message}`);
      console.error(err);
    } finally {
      setSpo2Loading(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Health Data Monitor
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
          Connected to backend: {API_URL} (For experimental purposes)
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <Box sx={{
                display: 'flex',
                flexDirection: { xs: 'column', md: 'row' },
                alignItems: { xs: 'stretch', md: 'flex-end' },
                gap: 3,
                justifyContent: 'space-between',
                mb: 3
              }}>
                <UserSelector
                  users={users}
                  selectedUser={selectedUser}
                  onChange={setSelectedUser}
                  isLoading={loading}
                />

                <DateRangePicker
                  startDate={startDate}
                  endDate={endDate}
                  onStartDateChange={setStartDate}
                  onEndDateChange={setEndDate}
                />
              </Box>

              <Box sx={{
                display: 'flex',
                justifyContent: 'center',
                mt: 3
              }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleVisualizeAll}
                  disabled={!selectedUser || loading || visualizationLoading}
                  sx={{ py: 1.5, px: 4 }}
                >
                  {visualizationLoading ? 'Loading...' : 'Visualize All Health Data'}
                </Button>
              </Box>
            </>
          )}
        </Paper>

        {selectedUser && (
          <Box sx={{ mt: 2, mb: 4 }}>
            <Typography variant="h6">
              Selected Parameters:
            </Typography>
            <Typography variant="body1">
              User ID: {selectedUser}, Date Range: {startDate} to {endDate}
            </Typography>
          </Box>
        )}

        {showAllVisualizations && (
          <>
            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Heart Rate Analysis
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Daily average heart rate values with resting heart rate comparison
              </Typography>
              <HeartRateChart
                data={heartRateData}
                loading={heartRateLoading}
                error={heartRateError}
              />
            </Paper>

            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Heart Rate Zone Distribution
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Time spent in each heart rate zone per day
              </Typography>
              <HeartRateZoneChart
                data={zoneData}
                loading={zoneLoading}
                error={zoneError}
              />
            </Paper>

            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Blood Oxygen (SpO2) Analysis
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Daily average SpO2 levels with normal range indicators
              </Typography>
              <SpO2Chart
                data={spo2Data}
                loading={spo2Loading}
                error={spo2Error}
              />
            </Paper>
          </>
        )}
      </Box>
    </Container>
  );
}

export default App;