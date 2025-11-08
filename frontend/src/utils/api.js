/**
 * API Utility Functions
 * Handles authenticated API calls to the backend
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Get auth token from localStorage
 */
function getAuthToken() {
  return localStorage.getItem('session_token');
}

/**
 * Handle API errors and redirect to login if unauthorized
 */
function handleApiError(response) {
  if (response.status === 401) {
    // Token expired or invalid - clear auth and redirect
    localStorage.removeItem('session_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('Session expired. Please login again.');
  }

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response;
}

/**
 * Upload audio file for transcription (authenticated)
 */
export async function uploadAudio(audioBlob) {
  const token = getAuthToken();

  if (!token) {
    throw new Error('Not authenticated');
  }

  const formData = new FormData();
  formData.append('file', audioBlob, 'recording.webm');

  const response = await fetch(`${API_BASE_URL}/api/transcribe`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  handleApiError(response);

  return response.json();
}

/**
 * Get current user info (authenticated)
 */
export async function getCurrentUser() {
  const token = getAuthToken();

  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  handleApiError(response);

  return response.json();
}

/**
 * Generic authenticated fetch helper
 */
export async function authenticatedFetch(endpoint, options = {}) {
  const token = getAuthToken();

  if (!token) {
    throw new Error('Not authenticated');
  }

  const defaultHeaders = {
    'Authorization': `Bearer ${token}`,
    ...(options.headers || {})
  };

  // Don't add Content-Type if FormData (browser sets it automatically)
  if (!(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: defaultHeaders
  });

  handleApiError(response);

  return response.json();
}
