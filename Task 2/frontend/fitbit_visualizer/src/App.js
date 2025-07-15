import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Paper, CircularProgress, Alert } from '@mui/material';
import UserSelector from './components/UserSelector';
import DateRangePicker from './components/DateRangePicker';
import { API_URL } from './services/api';
import { fetchUsers } from './services/users_api';
import './App.css';

function App() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-01-31');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
            <Box sx={{
              display: 'flex',
              flexDirection: { xs: 'column', md: 'row' },
              alignItems: { xs: 'stretch', md: 'flex-end' },
              gap: 3,
              justifyContent: 'space-between'
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
          )}
        </Paper>

        {selectedUser && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6">
              Selected Parameters:
            </Typography>
            <Typography variant="body1">
              User ID: {selectedUser}, Date Range: {startDate} to {endDate}
            </Typography>
          </Box>
        )}
      </Box>
    </Container>
  );
}

export default App;