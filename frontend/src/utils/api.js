/**
 * API client utility with authentication support
 * Automatically attaches JWT tokens and handles 401 responses
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

/**
 * Get the authentication token from localStorage
 */
export const getAuthToken = () => {
  return localStorage.getItem('auth_token');
};

/**
 * Set the authentication token in localStorage
 */
export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
};

/**
 * Remove the authentication token
 */
export const clearAuthToken = () => {
  localStorage.removeItem('auth_token');
};

/**
 * Make an authenticated API request
 * @param {string} endpoint - API endpoint (e.g., '/auth/me')
 * @param {object} options - Fetch options (method, body, headers, etc.)
 * @returns {Promise} - Fetch promise
 */
export const apiRequest = async (endpoint, options = {}) => {
  const token = getAuthToken();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add authorization header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers,
  };

  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, config);

    // Handle 401 Unauthorized - redirect to login
    if (response.status === 401) {
      clearAuthToken();
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    // Handle other HTTP errors
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP Error: ${response.status}`);
    }

    // Return response for successful requests
    return response;
  } catch (error) {
    console.error('API Request Error:', error);
    throw error;
  }
};

/**
 * GET request
 */
export const get = async (endpoint) => {
  const response = await apiRequest(endpoint, { method: 'GET' });
  return response.json();
};

/**
 * POST request
 */
export const post = async (endpoint, data) => {
  const response = await apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return response.json();
};

/**
 * PUT request
 */
export const put = async (endpoint, data) => {
  const response = await apiRequest(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  return response.json();
};

/**
 * DELETE request
 */
export const del = async (endpoint) => {
  const response = await apiRequest(endpoint, { method: 'DELETE' });
  return response.json();
};

export default {
  get,
  post,
  put,
  del,
  apiRequest,
  getAuthToken,
  setAuthToken,
  clearAuthToken,
};
