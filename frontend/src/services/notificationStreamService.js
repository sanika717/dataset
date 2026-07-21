import { tokenStorage } from "./api";

/**
 * Assumed backend contract (adjust here if your routes differ — unbuilt on
 * the backend side as of Phase 6, same caveat as streamService.js):
 *
 *   WS  /api/notifications/stream?token={jwt}
 *
 *   Token travels as a query param for the same reason as the camera
 *   stream — no custom headers on a WebSocket handshake from the browser.
 *
 *   Server -> client messages, JSON text frames:
 *     - new notification:
 *         { "type": "notification", "notification": { ...Notification } }
 *     - an existing notification changed (e.g. marked read on another
 *       device/tab):
 *         { "type": "notification_updated", "notification": { ... } }
 *     - a notification was removed:
 *         { "type": "notification_deleted", "id": 123 }
 *     - periodic keepalive (safe to ignore):
 *         { "type": "ping" }
 *
 *   Client -> server: nothing required; receive-only from the frontend.
 */

function wsBaseUrl() {
  const httpBase =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
  return httpBase.replace(/^http/, "ws").replace(/\/$/, "");
}

export function getNotificationStreamUrl() {
  const token = tokenStorage.get();
  const params = new URLSearchParams();
  if (token) params.set("token", token);
  return `${wsBaseUrl()}/api/notifications/stream?${params.toString()}`;
}

export default { getNotificationStreamUrl };
