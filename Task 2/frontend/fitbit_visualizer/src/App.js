import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Paper, CircularProgress, Alert, Button } from '@mui/material';
import UserSelector from './components/UserSelector';
import DateRangePicker from './components/DateRangePicker';
import HeartRateChart from './components/HeartRateChart';
import HeartRateZoneChart from './components/HeartRateZoneChart';
import SpO2Chart from './components/SpO2Chart';
import HRVChart from './components/HRVChart';
import HRVScatterChart from './components/HRVScatterChart';
import BreathingRateChart from './components/BreathingRateChart';
import BreathingRateBarChart from './components/BreathingRateBarChart';
import AZMStackedChart from './components/AZMStackedChart';
import AZMLineChart from './components/AZMLineChart';
import ActivityLineChart from './components/ActivityLineChart';
import ActivityBarChart from './components/ActivityBarChart';
import { API_URL } from './services/api';
import { fetchUsers } from './services/users_api';
import { fetchDailyAvgHeartRateData, fetchHeartRateZonesData } from './services/heartRate_api';
import { fetchDailyAvgSpO2Data } from './services/spo2_api';
import { fetchDailyAvgHRVData } from './services/hrv_api';
import { fetchAllBreathingRateData } from './services/breathingRate_api';
import { fetchDailyAvgAZMData } from './services/azm_api';
import { fetchAllActivityData } from './services/activity_api';
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

  const [hrvData, setHrvData] = useState([]);
  const [hrvLoading, setHrvLoading] = useState(false);
  const [hrvError, setHrvError] = useState(null);

  const [breathingRateData, setBreathingRateData] = useState([]);
  const [breathingRateLoading, setBreathingRateLoading] = useState(false);
  const [breathingRateError, setBreathingRateError] = useState(null);

  const [azmData, setAzmData] = useState([]);
  const [azmLoading, setAzmLoading] = useState(false);
  const [azmError, setAzmError] = useState(null);

  const [activityData, setActivityData] = useState([]);
  const [activityLoading, setActivityLoading] = useState(false);
  const [activityError, setActivityError] = useState(null);

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
      setHrvError("Please select a user");
      setBreathingRateError("Please select a user");
      setAzmError("Please select a user");
      setActivityError("Please select a user");
      return;
    }

    setVisualizationLoading(true);
    setShowAllVisualizations(true);

    await Promise.all([
      fetchHeartRateData(),
      fetchZoneData(),
      fetchSpO2Data(),
      fetchHRVData(),
      fetchBreathingRateData(),
      fetchAZMData(),
      fetchActivityData()
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

  const fetchHRVData = async () => {
    setHrvLoading(true);
    setHrvError(null);

    try {
      const response = await fetchDailyAvgHRVData(selectedUser, startDate, endDate);

      if (response.success) {
        const processedData = response.data.map(item => ({
          timestamp: new Date(item.day).getTime(),
          rmssd: item.avg_rmssd,
          coverage: item.avg_coverage,
          hf: item.avg_hf,
          lf: item.avg_lf
        })).sort((a, b) => a.timestamp - b.timestamp);

        setHrvData(processedData);

        if (response.warning) {
          setHrvError(response.warning);
        } else {
          setHrvError(null);
        }
      } else {
        setHrvError('Failed to fetch HRV data');
      }
    } catch (err) {
      setHrvError(`Error fetching HRV data: ${err.message}`);
      console.error(err);
    } finally {
      setHrvLoading(false);
    }
  };

  const fetchBreathingRateData = async () => {
    setBreathingRateLoading(true);
    setBreathingRateError(null);

    try {
      const response = await fetchAllBreathingRateData(selectedUser, startDate, endDate);

      if (response.success) {
        const processedData = response.data.map(item => ({
          timestamp: new Date(item.timestamp).getTime(),
          deep_sleep_rate: item.deep_sleep_rate,
          rem_sleep_rate: item.rem_sleep_rate,
          light_sleep_rate: item.light_sleep_rate,
          full_sleep_rate: item.full_sleep_rate
        })).sort((a, b) => a.timestamp - b.timestamp);

        setBreathingRateData(processedData);

        if (response.warning) {
          setBreathingRateError(response.warning);
        } else {
          setBreathingRateError(null);
        }
      } else {
        setBreathingRateError('Failed to fetch breathing rate data');
      }
    } catch (err) {
      setBreathingRateError(`Error fetching breathing rate data: ${err.message}`);
      console.error(err);
    } finally {
      setBreathingRateLoading(false);
    }
  };

  const fetchAZMData = async () => {
    setAzmLoading(true);
    setAzmError(null);

    try {
      const response = await fetchDailyAvgAZMData(selectedUser, startDate, endDate);

      if (response.success) {
        const processedData = response.data.map(item => ({
          timestamp: new Date(item.day).getTime(),
          fat_burn: item.avg_fat_burn_minutes,
          cardio: item.avg_cardio_minutes,
          peak: item.avg_peak_minutes,
          total_azm: item.avg_active_zone_minutes
        })).sort((a, b) => a.timestamp - b.timestamp);

        setAzmData(processedData);

        if (response.warning) {
          setAzmError(response.warning);
        } else {
          setAzmError(null);
        }
      } else {
        setAzmError('Failed to fetch AZM data');
      }
    } catch (err) {
      setAzmError(`Error fetching AZM data: ${err.message}`);
      console.error(err);
    } finally {
      setAzmLoading(false);
    }
  };

  const fetchActivityData = async () => {
    setActivityLoading(true);
    setActivityError(null);

    try {
      const response = await fetchAllActivityData(selectedUser, startDate, endDate);

      if (response.success) {
        const processedData = response.data.map(item => ({
          timestamp: new Date(item.timestamp).getTime(),
          steps: item.value
        })).sort((a, b) => a.timestamp - b.timestamp);

        setActivityData(processedData);

        if (response.warning) {
          setActivityError(response.warning);
        } else {
          setActivityError(null);
        }
      } else {
        setActivityError('Failed to fetch activity data');
      }
    } catch (err) {
      setActivityError(`Error fetching activity data: ${err.message}`);
      console.error(err);
    } finally {
      setActivityLoading(false);
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

            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Heart Rate Variability (HRV) - RMSSD Trend
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                RMSSD values over time with 7-day moving average and coverage quality
              </Typography>
              <HRVChart
                data={hrvData}
                loading={hrvLoading}
                error={hrvError}
              />
            </Paper>

            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Heart Rate Variability (HRV) - Frequency Domain Analysis
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                High Frequency (HF) vs Low Frequency (LF) power analysis
              </Typography>
              <HRVScatterChart
                data={hrvData}
                loading={hrvLoading}
                error={hrvError}
              />
            </Paper>

            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Breathing Rate Analysis - Sleep Phases
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Breathing rates during different sleep phases over time
              </Typography>
              <BreathingRateChart
                data={breathingRateData}
                loading={breathingRateLoading}
                error={breathingRateError}
              />
            </Paper>

            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Breathing Rate Comparison - By Sleep Phase
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Comparative view of breathing rates across different sleep phases
              </Typography>
              <BreathingRateBarChart
                data={breathingRateData}
                loading={breathingRateLoading}
                error={breathingRateError}
              />
            </Paper>

            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Active Zone Minutes - Stacked Distribution
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Daily breakdown of minutes spent in different heart rate zones
              </Typography>
              <AZMStackedChart
                data={azmData}
                loading={azmLoading}
                error={azmError}
              />
            </Paper>

            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Active Zone Minutes - Trend Analysis
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Trends in active zone minutes across different intensity levels
              </Typography>
              <AZMLineChart
                data={azmData}
                loading={azmLoading}
                error={azmError}
              />
            </Paper>

            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Daily Activity - Step Count Trends
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Daily step count with 7-day moving average and activity level indicators
              </Typography>
              <ActivityLineChart
                data={activityData}
                loading={activityLoading}
                error={activityError}
              />
            </Paper>

            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Daily Activity - Step Count Distribution
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Daily step count with color-coded activity levels
              </Typography>
              <ActivityBarChart
                data={activityData}
                loading={activityLoading}
                error={activityError}
              />
            </Paper>
          </>
        )}
      </Box>
    </Container>
  );
}

export default App;