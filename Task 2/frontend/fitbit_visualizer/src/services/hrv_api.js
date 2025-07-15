import { API_URL } from './api';

export const fetchDailyAvgHRVData = async (userId, startDate, endDate) => {
    try {
        const response = await fetch(`${API_URL}/api/hrv/get_daily_avg_hrv_data?user_id=${userId}&start_date=${startDate}&end_date=${endDate}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch daily average HRV data:', error);
        throw error;
    }
};