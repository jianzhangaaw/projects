import http from './http'
import type { Notification, PageResult } from '@/types/api'

export function listNotifications(params: { current?: number; size?: number; isRead?: number } = {}) {
  return http.get<unknown, PageResult<Notification>>('/notifications', { params })
}

// receiverId 由后端从 JWT 当前用户获取，前端不再传
export function listMyNotifications() {
  return http.get<unknown, Notification[]>('/notifications/mine')
}

export function markNotificationRead(id: number) {
  return http.patch<unknown, void>(`/notifications/${id}/read`)
}

export function markAllNotificationsRead() {
  return http.patch<unknown, void>('/notifications/read-all')
}

export function getUnreadCount() {
  return http.get<unknown, number>('/notifications/unread-count')
}
