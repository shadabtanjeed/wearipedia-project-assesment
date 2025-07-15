import React from 'react';
import { TextField, Box } from '@mui/material';

const DateRangePicker = ({ startDate, endDate, onStartDateChange, onEndDateChange }) => {
    // Define date constraints
    const minDate = '2024-01-01';
    const maxDate = '2024-01-31';

    const validateDate = (date) => {
        const selectedDate = new Date(date);
        const minDateTime = new Date(minDate);
        const maxDateTime = new Date(maxDate);

        return selectedDate >= minDateTime && selectedDate <= maxDateTime;
    };

    const handleStartDateChange = (e) => {
        const newDate = e.target.value;
        if (validateDate(newDate)) {
            onStartDateChange(newDate);
        } else {
            alert(`Please select a date between January 1, 2024 and January 31, 2024`);
        }
    };

    const handleEndDateChange = (e) => {
        const newDate = e.target.value;
        if (validateDate(newDate)) {
            onEndDateChange(newDate);
        } else {
            alert(`Please select a date between January 1, 2024 and January 31, 2024`);
        }
    };

    return (
        <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
                label="Start Date"
                type="date"
                value={startDate}
                onChange={handleStartDateChange}
                InputLabelProps={{ shrink: true }}
                inputProps={{ min: minDate, max: maxDate }}
            />

            <TextField
                label="End Date"
                type="date"
                value={endDate}
                onChange={handleEndDateChange}
                InputLabelProps={{ shrink: true }}
                inputProps={{ min: minDate, max: maxDate }}
            />
        </Box>
    );
};

export default DateRangePicker;