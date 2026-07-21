import apiClient from "./api";

/**
 * Assumed backend contract (adjust here if your routes differ):
 *   GET   /api/notifications                 -> [Notification]
 *   GET   /api/notifications/unread-count     -> { count }
 *   PUT   /api/notifications/{id}/read        -> Notification
 *   PUT   /api/notifications/read-all         -> { updated: n }
 *   DELETE /api/notifications/{id}            -> 204
 */

export async function getNotifications({ skip = 0, limit = 50, unreadOnly = false } = {}) {
  const { data } = await apiClient.get("/api/notifications", {
    params: { skip, limit, unread_only: unreadOnly },
  });
  return data;
}

export async function getUnreadCount() {
  const { data } = await apiClient.get("/api/notifications/unread-count");
  return data.count ?? 0;
}

export async function markAsRead(id) {
  const { data } = await apiClient.put(`/api/notifications/${id}/read`);
  return data;
}

export async function markAllAsRead() {
  const { data } = await apiClient.put("/api/notifications/read-all");
  return data;
}

export async function deleteNotification(id) {
  await apiClient.delete(`/api/notifications/${id}`);
  return id;
}
