import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Notification, NotificationType } from '@/types/api'

// ─── Notification Store ───────────────────────────────────────────────────────

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])

  function add(
    type: NotificationType,
    title: string,
    message?: string,
    duration = 4000,
  ): string {
    // Suppress duplicate — same type + title + message already visible
    const isDupe = notifications.value.some(
      (n) => n.type === type && n.title === title && n.message === message,
    )
    if (isDupe) return ''

    const id = `notif-${Date.now()}-${Math.random().toString(36).slice(2)}`
    notifications.value.push({ id, type, title, message, duration, timestamp: Date.now() })

    if (duration > 0) {
      setTimeout(() => remove(id), duration)
    }
    return id
  }

  function remove(id: string) {
    const idx = notifications.value.findIndex((n) => n.id === id)
    if (idx !== -1) notifications.value.splice(idx, 1)
  }

  function clear() {
    notifications.value = []
  }

  // Convenience helpers
  const success = (title: string, message?: string) => add('success', title, message)
  const error   = (title: string, message?: string) => add('error', title, message, 6000)
  const warning = (title: string, message?: string) => add('warning', title, message)
  const info    = (title: string, message?: string) => add('info', title, message)

  return { notifications, add, remove, clear, success, error, warning, info }
})
