import { API_URL } from './api';

// Fetch users from the API
export const fetchUsers = async () => {
    try {
        const response = await fetch(`${API_URL}/api/users/get_all_users`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch users:', error);
        throw error;
    }
};