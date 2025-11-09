import { authenticatedFetch } from '../utils/api';

export async function getUpcomingNotifications(userId, days = 7) {
  const query = new URLSearchParams();
  if (userId) query.set('user_id', userId);
  if (days) query.set('days', String(days));
  const endpoint = `/api/notifications${query.toString() ? `?${query.toString()}` : ''}`;
  return authenticatedFetch(endpoint, { method: 'GET' });
}


export async function getWeeklyHighlights(userId) {
  const query = new URLSearchParams();
  if (userId) query.set('user_id', userId);
  const endpoint = `/api/notifications/highlights${query.toString() ? `?${query.toString()}` : ''}`;
  return authenticatedFetch(endpoint, { method: 'GET' });
}


