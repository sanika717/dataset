import { useCallback, useEffect, useRef, useState } from "react";

import {
  getNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  deleteNotification,
} from "../services/notificationService";
import { getNotificationStreamUrl } from "../services/notificationStreamService";

const MAX_BACKOFF_MS = 15000;
const BASE_BACKOFF_MS = 1000;
const POLL_WHEN_LIVE_MS = 120000; // slow heartbeat poll while WS is connected
const POLL_WHEN_DOWN_MS = 30000; // fall back to tighter polling if WS is unavailable

/**
 * Owns notification list + unread count, backed by a real-time WebSocket
 * (see notificationStreamService.js for the assumed contract) with REST
 * polling as a fallback/heartbeat. Set `realtime: false` to disable the
 * socket entirely and rely on polling alone.
 *
 * Usage:
 *   const {
 *     notifications, unreadCount, loading, error, realtimeStatus,
 *     refresh, markRead, markAllRead, remove,
 *   } = useNotifications();
 */
export function useNotifications({
  skip = 0,
  limit = 50,
  unreadOnly = false,
  realtime = true,
} = {}) {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [realtimeStatus, setRealtimeStatus] = useState("idle"); // idle | connecting | live | reconnecting | unavailable

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const attemptRef = useRef(0);
  const mountedRef = useRef(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [list, count] = await Promise.all([
        getNotifications({ skip, limit, unreadOnly }),
        getUnreadCount(),
      ]);
      setNotifications(list);
      setUnreadCount(count);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load notifications.");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [skip, limit, unreadOnly]);

  const refreshUnreadCount = useCallback(async () => {
    try {
      const count = await getUnreadCount();
      setUnreadCount(count);
    } catch (err) {
      console.error("Failed to refresh unread count:", err);
    }
  }, []);

  // --- REST actions -------------------------------------------------

  const markRead = useCallback(async (id) => {
    try {
      const updated = await markAsRead(id);
      setNotifications((prev) => prev.map((n) => (n.id === id ? updated : n)));
      setUnreadCount((prev) => Math.max(0, prev - 1));
      return updated;
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to mark as read.");
      throw err;
    }
  }, []);

  const markAllRead = useCallback(async () => {
    try {
      await markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to mark all as read.");
      throw err;
    }
  }, []);

  const remove = useCallback(async (id) => {
    try {
      await deleteNotification(id);
      setNotifications((prev) => {
        const target = prev.find((n) => n.id === id);
        if (target && !target.read) {
          setUnreadCount((count) => Math.max(0, count - 1));
        }
        return prev.filter((n) => n.id !== id);
      });
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete notification.");
      throw err;
    }
  }, []);

  // --- WebSocket push -------------------------------------------------

  const applyPushedNotification = useCallback((notification) => {
    setNotifications((prev) => {
      if (prev.some((n) => n.id === notification.id)) return prev;
      return [notification, ...prev];
    });
    if (!notification.read) {
      setUnreadCount((prev) => prev + 1);
    }
  }, []);

  const applyUpdatedNotification = useCallback((notification) => {
    setNotifications((prev) => {
      const existing = prev.find((n) => n.id === notification.id);
      if (existing && !existing.read && notification.read) {
        setUnreadCount((count) => Math.max(0, count - 1));
      }
      return prev.map((n) => (n.id === notification.id ? notification : n));
    });
  }, []);

  const applyDeletedNotification = useCallback((id) => {
    setNotifications((prev) => {
      const target = prev.find((n) => n.id === id);
      if (target && !target.read) {
        setUnreadCount((count) => Math.max(0, count - 1));
      }
      return prev.filter((n) => n.id !== id);
    });
  }, []);

  const clearReconnectTimer = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  };

  const setPollInterval = useCallback(
    (ms) => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = setInterval(refreshUnreadCount, ms);
    },
    [refreshUnreadCount]
  );

  const connectSocket = useCallback(() => {
    if (!realtime) return;
    clearReconnectTimer();
    setRealtimeStatus((prev) => (prev === "live" ? prev : "connecting"));

    let socket;
    try {
      socket = new WebSocket(getNotificationStreamUrl());
    } catch {
      setRealtimeStatus("unavailable");
      setPollInterval(POLL_WHEN_DOWN_MS);
      return;
    }
    wsRef.current = socket;

    socket.onopen = () => {
      if (!mountedRef.current) return;
      attemptRef.current = 0;
      setRealtimeStatus("live");
      setPollInterval(POLL_WHEN_LIVE_MS); // heartbeat only — WS carries the real updates
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "notification" && msg.notification) {
          applyPushedNotification(msg.notification);
        } else if (msg.type === "notification_updated" && msg.notification) {
          applyUpdatedNotification(msg.notification);
        } else if (msg.type === "notification_deleted" && msg.id != null) {
          applyDeletedNotification(msg.id);
        }
        // "ping" and anything unrecognized are ignored.
      } catch {
        // Non-JSON payload — ignore rather than crash the handler.
      }
    };

    socket.onclose = (event) => {
      if (!mountedRef.current) return;
      wsRef.current = null;
      if (!realtime || event.code === 4401) {
        setRealtimeStatus("unavailable");
        setPollInterval(POLL_WHEN_DOWN_MS);
        return;
      }
      setRealtimeStatus("reconnecting");
      setPollInterval(POLL_WHEN_DOWN_MS);
      const delay = Math.min(MAX_BACKOFF_MS, BASE_BACKOFF_MS * 2 ** attemptRef.current);
      attemptRef.current += 1;
      reconnectTimeoutRef.current = setTimeout(connectSocket, delay);
    };

    socket.onerror = () => {
      // onclose fires right after and handles reconnect/backoff.
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [realtime, applyPushedNotification, applyUpdatedNotification, applyDeletedNotification, setPollInterval]);

  useEffect(() => {
    mountedRef.current = true;
    refresh();

    if (realtime) {
      connectSocket();
    } else {
      setRealtimeStatus("unavailable");
      setPollInterval(POLL_WHEN_DOWN_MS);
    }

    return () => {
      mountedRef.current = false;
      clearReconnectTimer();
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [skip, limit, unreadOnly, realtime]);

  return {
    notifications,
    unreadCount,
    loading,
    error,
    realtimeStatus,
    refresh,
    refreshUnreadCount,
    markRead,
    markAllRead,
    remove,
  };
}

export default useNotifications;
