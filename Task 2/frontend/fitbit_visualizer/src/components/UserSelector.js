import React from 'react';
import { FormControl, InputLabel, Select, MenuItem, Box } from '@mui/material';

const UserSelector = ({ users, selectedUser, onChange, isLoading }) => {
    return (
        <Box sx={{ minWidth: 200, maxWidth: 300 }}>
            <FormControl fullWidth variant="outlined" disabled={isLoading}>
                <InputLabel id="user-select-label">User</InputLabel>
                <Select
                    labelId="user-select-label"
                    id="user-select"
                    value={selectedUser || ''}
                    label="User"
                    onChange={(e) => onChange(e.target.value)}
                >
                    {users.map((user) => (
                        <MenuItem key={user.user_id} value={user.user_id}>
                            User {user.user_id} - {user.name}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>
        </Box>
    );
};

export default UserSelector;