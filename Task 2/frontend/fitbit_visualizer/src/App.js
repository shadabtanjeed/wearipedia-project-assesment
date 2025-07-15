import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Paper, CircularProgress, Alert, Button } from '@mui/material';
import UserSelector from './components/UserSelector';
import DateRangePicker from './components/DateRangePicker';
import HeartRateChart from './components/HeartRateChart';
import { API_URL } from './services/api';
import { fetchUsers } from './services/users_api';
import { fetchDailyAvgHeartRateData } from './services/heartRate_api';
import './App.css';

function App() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-01-31');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [healthData, setHealthData] = useState([]);
  const [dataLoading, setDataLoading] = useState(false);
  const [dataError, setDataError] = useState(null);
  const [showVisualization, setShowVisualization] = useState(false);

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

  const handleVisualize = async () => {
    if (!selectedUser) {
      setDataError("Please select a user");
      return;
    }

    setDataLoading(true);
    setDataError(null);
    setShowVisualization(true);

    try {
      // Using daily average by default
      const response = await fetchDailyAvgHeartRateData(selectedUser, startDate, endDate);

      if (response.success) {
        // Process data to ensure timestamp is in the right format for charts
        const processedData = response.data.map(item => ({
          timestamp: new Date(item.day).getTime(),
          value: item.avg_heart_rate,
          resting_heart_rate: item.avg_resting_heart_rate
        })).sort((a, b) => a.timestamp - b.timestamp);

        setHealthData(processedData);

        if (response.warning) {
          setDataError(response.warning);
        } else {
          setDataError(null);
        }
      } else {
        setDataError('Failed to fetch health data');
      }
    } catch (err) {
      setDataError(`Error fetching health data: ${err.message}`);
      console.error(err);
    } finally {
      setDataLoading(false);
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
                  onClick={handleVisualize}
                  disabled={!selectedUser || loading}
                  sx={{ py: 1.5, px: 4 }}
                >
                  Visualize Health Data
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

        {showVisualization && (
          <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
            <Typography variant="h5" gutterBottom>
              Heart Rate Visualization
            </Typography>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Daily average heart rate values
            </Typography>
            <HeartRateChart
              data={healthData}
              loading={dataLoading}
              error={dataError}
            />
          </Paper>
        )}
      </Box>
    </Container>
  );
}

export default App;