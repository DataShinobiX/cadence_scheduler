import { authenticatedFetch } from '../utils/api';

export async function getUserPreferences() {
  return authenticatedFetch('/api/user/preferences', {
    method: 'GET'
  });
}

export async function saveUserPreferences(preferences) {
  return authenticatedFetch('/api/user/preferences', {
    method: 'PATCH',
    body: JSON.stringify({ preferences })
  });
}
