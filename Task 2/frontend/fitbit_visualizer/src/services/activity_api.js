import { API_URL } from './api';

export const fetchAllActivityData = async (userId, startDate, endDate) => {
    try {
        const response = await fetch(`${API_URL}/api/activity/get_all_activity_data?user_id=${userId}&start_date=${startDate}&end_date=${endDate}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch activity data:', error);
        throw error;
    }
};