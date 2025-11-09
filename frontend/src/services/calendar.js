/**
 * Calendar Service
 * Handles fetching calendar events from the backend
 */

import { authenticatedFetch } from '../utils/api';

/**
 * Fetch calendar events for the authenticated user
 * @param {string} startDate - Start date in YYYY-MM-DD format (optional)
 * @param {string} endDate - End date in YYYY-MM-DD format (optional)
 * @param {number} days - Number of days to fetch if endDate not provided (default: 30)
 * @returns {Promise<Object>} Calendar events response
 */
export async function fetchCalendarEvents(startDate = null, endDate = null, days = 30) {
  try {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (days) params.append('days', days.toString());

    const queryString = params.toString();
    const endpoint = `/api/calendar/events${queryString ? `?${queryString}` : ''}`;

    const response = await authenticatedFetch(endpoint, {
      method: 'GET',
    });

    return response;
  } catch (error) {
    console.error('Error fetching calendar events:', error);
    throw error;
  }
}

/**
 * Format event for display
 * @param {Object} event - Calendar event object
 * @returns {Object} Formatted event
 */
export function formatEvent(event) {
  const start = new Date(event.start_datetime);
  const end = new Date(event.end_datetime);

  return {
    ...event,
    start,
    end,
    date: start.toISOString().split('T')[0],
    startTime: start.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
    endTime: end.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
    duration: Math.round((end - start) / (1000 * 60)), // Duration in minutes
  };
}

/**
 * Group events by date
 * @param {Array} events - Array of calendar events
 * @returns {Object} Events grouped by date (YYYY-MM-DD)
 */
export function groupEventsByDate(events) {
  const grouped = {};

  events.forEach(event => {
    const formatted = formatEvent(event);
    const dateKey = formatted.date;

    if (!grouped[dateKey]) {
      grouped[dateKey] = [];
    }

    grouped[dateKey].push(formatted);
  });

  // Sort events within each date by start time
  Object.keys(grouped).forEach(date => {
    grouped[date].sort((a, b) => a.start - b.start);
  });

  return grouped;
}

