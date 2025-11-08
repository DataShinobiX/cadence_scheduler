

import { useState, useCallback } from 'react';

export default function useNotification() {
  const [isOpen, setIsOpen] = useState(false);
  const [notification, setNotification] = useState({
    title: '',
    message: '',
  });

  const showNotification = useCallback((title, message) => {
    setNotification({ title, message });
    setIsOpen(true);
  }, []);

  const closeNotification = useCallback(() => {
    setIsOpen(false);
  }, []);

  return {
    isOpen,
    title: notification.title,
    message: notification.message,
    showNotification,
    closeNotification,
  };
}