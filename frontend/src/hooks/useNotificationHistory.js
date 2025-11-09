import { useState, useEffect } from 'react';

const STORAGE_KEY = 'notification_history';
const MAX_NOTIFICATIONS = 50; // Keep last 50 notifications

export function useNotificationHistory() {
  const [notifications, setNotifications] = useState([]);

  // Load notifications from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setNotifications(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to load notification history:', e);
      }
    }
  }, []);

  // Add a notification to history
  const addNotification = (message, type = 'info') => {
    const newNotification = {
      id: Date.now() + Math.random(),
      message,
      type,
      timestamp: new Date().toISOString(),
      read: false,
    };

    setNotifications((prev) => {
      const updated = [newNotification, ...prev].slice(0, MAX_NOTIFICATIONS);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  };

  // Mark notification as read
  const markAsRead = (id) => {
    setNotifications((prev) => {
      const updated = prev.map((notif) =>
        notif.id === id ? { ...notif, read: true } : notif
      );
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  };

  // Mark all as read
  const markAllAsRead = () => {
    setNotifications((prev) => {
      const updated = prev.map((notif) => ({ ...notif, read: true }));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  };

  // Delete a notification
  const deleteNotification = (id) => {
    setNotifications((prev) => {
      const updated = prev.filter((notif) => notif.id !== id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  };

  // Clear all notifications
  const clearAll = () => {
    setNotifications([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return {
    notifications,
    unreadCount,
    addNotification,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll,
  };
}
