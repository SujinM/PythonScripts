import { useNotificationStore } from '@/stores/notificationStore'

/**
 * Thin composable wrapper around the notification store for
 * convenient use in templates and component setup functions.
 */
export function useNotification() {
  const store = useNotificationStore()
  return {
    notifications: store.notifications,
    success: store.success,
    error:   store.error,
    warning: store.warning,
    info:    store.info,
    remove:  store.remove,
    clear:   store.clear,
  }
}
