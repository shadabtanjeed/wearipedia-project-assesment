import { API_URL } from './api';

export const fetchDailyAvgHeartRateData = async (userId, startDate, endDate) => {
    try {
        const response = await fetch(`${API_URL}/api/heart_rate/get_daily_avg_heart_rate_data?user_id=${userId}&start_date=${startDate}&end_date=${endDate}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch daily average heart rate data:', error);
        throw error;
    }
};

export const fetchAllHeartRateData = async (userId, startDate, endDate) => {
    try {
        const response = await fetch(`${API_URL}/api/heart_rate/get_all_heart_rate_data?user_id=${userId}&start_date=${startDate}&end_date=${endDate}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch all heart rate data:', error);
        throw error;
    }
};

export const fetchHeartRateZonesData = async (userId, startDate, endDate) => {
    try {
        const response = await fetch(`${API_URL}/api/heart_rate/get_heart_rate_zones_data?user_id=${userId}&start_date=${startDate}&end_date=${endDate}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch heart rate zones data:', error);
        throw error;
    }
};