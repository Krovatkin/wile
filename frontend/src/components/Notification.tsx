// Notification/Toast component

import type { Notification, NotificationType } from '@/types';

interface NotificationProps {
  notification: Notification;
  onClose: (id: string) => void;
}

function getAlertClass(type: NotificationType): string {
  switch (type) {
    case 'success':
      return 'alert-success';
    case 'error':
      return 'alert-error';
    case 'warning':
      return 'alert-warning';
    case 'info':
    default:
      return 'alert-info';
  }
}

export function NotificationItem({ notification, onClose }: NotificationProps) {
  return (
    <div className={`alert ${getAlertClass(notification.type)} shadow-lg mb-2`}>
      <div>
        <span>{notification.message}</span>
      </div>
      <button
        className="btn btn-sm btn-ghost"
        onClick={() => onClose(notification.id)}
      >
        ✕
      </button>
    </div>
  );
}

interface NotificationContainerProps {
  notifications: Notification[];
  onClose: (id: string) => void;
}

export function NotificationContainer({ notifications, onClose }: NotificationContainerProps) {
  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 w-96">
      {notifications.map(notification => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClose={onClose}
        />
      ))}
    </div>
  );
}
