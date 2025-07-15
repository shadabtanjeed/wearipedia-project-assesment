import { API_URL } from './api';

export const fetchAllBreathingRateData = async (userId, startDate, endDate) => {
    try {
        const response = await fetch(`${API_URL}/api/breathing_rate/get_all_breathing_rate_data?user_id=${userId}&start_date=${startDate}&end_date=${endDate}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch breathing rate data:', error);
        throw error;
    }
};