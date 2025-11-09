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
async function handleApiError(response, skipLogout = false) {
  if (response.status === 401) {
    // Check if it's a Google Calendar/Gmail not connected error
    try {
      const errorData = await response.clone().json();
      const detail = errorData.detail || '';

      // Check for various Google connection errors
      if (detail.includes('Google Calendar not connected') ||
          detail.includes('Gmail not connected') ||
          detail.includes('google_calendar_token') ||
          detail.includes('Please connect your Google Calendar') ||
          detail.includes('No calendar token found') ||
          detail.includes('No gmail token found')) {
        // Don't logout - throw error with status code so frontend can detect it
        const error = new Error('401: ' + detail);
        error.status = 401;
        throw error;
      }
    } catch (e) {
      // If it's already our custom error, re-throw it
      if (e.status === 401) {
        throw e;
      }
      // Otherwise, continue with normal 401 handling
    }

    // Only logout if not skipped (for calendar errors)
    if (!skipLogout) {
      // Token expired or invalid - clear auth and redirect
      localStorage.removeItem('session_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
      throw new Error('Session expired. Please login again.');
    }
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

  await handleApiError(response);

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

  await handleApiError(response);

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

  await handleApiError(response);

  return response.json();
}
