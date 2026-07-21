import { useCallback, useEffect, useRef, useState } from "react";

import { getCameraStreamUrl } from "../services/streamService";

const MAX_BACKOFF_MS = 15000;
const BASE_BACKOFF_MS = 1000;

/**
 * Owns the WebSocket lifecycle for one camera's live stream.
 *
 * Handles JSON frame messages (`{ type: "frame", image, detections,
 * timestamp }`) as well as raw binary JPEG frames — see streamService.js
 * for the assumed wire contract. Reconnects with exponential backoff
 * (capped at 15s) while `enabled` stays true; tears the socket down
 * cleanly on unmount or when `enabled` flips to false.
 *
 * Usage:
 *   const { status, frame, detections, fps, error, reconnect } =
 *     useCameraStream(cameraId, { enabled: isVisible });
 */
export function useCameraStream(cameraId, { enabled = true } = {}) {
  const [status, setStatus] = useState("idle"); // idle | connecting | live | reconnecting | error | closed
  const [frame, setFrame] = useState(null);
  const [detections, setDetections] = useState([]);
  const [lastFrameAt, setLastFrameAt] = useState(null);
  const [fps, setFps] = useState(0);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const attemptRef = useRef(0);
  const frameTimestampsRef = useRef([]);
  const objectUrlRef = useRef(null);
  const mountedRef = useRef(true);

  const clearReconnectTimer = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  };

  const revokePreviousObjectUrl = () => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  };

  const recordFrameForFps = () => {
    const now = performance.now();
    const buf = frameTimestampsRef.current;
    buf.push(now);
    while (buf.length && now - buf[0] > 2000) buf.shift();
    setFps(buf.length ? Math.round((buf.length / 2000) * 1000) : 0);
  };

  const handleMessage = useCallback((event) => {
    if (typeof event.data === "string") {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "frame" && msg.image) {
          revokePreviousObjectUrl();
          setFrame(msg.image);
          setDetections(msg.detections || []);
          setLastFrameAt(msg.timestamp ? new Date(msg.timestamp) : new Date());
          recordFrameForFps();
        } else if (msg.type === "detections") {
          // Binary-frame mode: detections arrive out-of-band from the image.
          setDetections(msg.detections || []);
        } else if (msg.type === "error") {
          setError(msg.message || "Stream error.");
        }
      } catch {
        // Not JSON — ignore rather than crash the socket handler.
      }
      return;
    }

    // Binary frame (Blob) — build an object URL for the <img>/<canvas>.
    const blob = event.data instanceof Blob ? event.data : new Blob([event.data]);
    revokePreviousObjectUrl();
    const url = URL.createObjectURL(blob);
    objectUrlRef.current = url;
    setFrame(url);
    setLastFrameAt(new Date());
    recordFrameForFps();
  }, []);

  const connect = useCallback(() => {
    if (!cameraId || !enabled) return;

    clearReconnectTimer();
    setStatus((prev) => (prev === "live" ? prev : "connecting"));
    setError(null);

    let socket;
    try {
      socket = new WebSocket(getCameraStreamUrl(cameraId));
    } catch (err) {
      setStatus("error");
      setError("Could not open stream connection.");
      return;
    }
    socket.binaryType = "blob";
    wsRef.current = socket;

    socket.onopen = () => {
      if (!mountedRef.current) return;
      attemptRef.current = 0;
      setStatus("live");
    };

    socket.onmessage = handleMessage;

    socket.onerror = () => {
      if (!mountedRef.current) return;
      setError("Stream connection error.");
    };

    socket.onclose = (event) => {
      if (!mountedRef.current) return;
      wsRef.current = null;
      if (!enabled || event.code === 4401) {
        setStatus(event.code === 4401 ? "error" : "closed");
        if (event.code === 4401) setError("Not authorized for this camera stream.");
        return;
      }
      // Auto-reconnect with exponential backoff.
      setStatus("reconnecting");
      const delay = Math.min(
        MAX_BACKOFF_MS,
        BASE_BACKOFF_MS * 2 ** attemptRef.current
      );
      attemptRef.current += 1;
      reconnectTimeoutRef.current = setTimeout(connect, delay);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cameraId, enabled, handleMessage]);

  const disconnect = useCallback(() => {
    clearReconnectTimer();
    if (wsRef.current) {
      wsRef.current.onclose = null; // don't trigger reconnect on manual close
      wsRef.current.close();
      wsRef.current = null;
    }
    revokePreviousObjectUrl();
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    attemptRef.current = 0;
    connect();
  }, [disconnect, connect]);

  useEffect(() => {
    mountedRef.current = true;
    if (enabled && cameraId) {
      connect();
    } else {
      disconnect();
      setStatus("idle");
    }
    return () => {
      mountedRef.current = false;
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cameraId, enabled]);

  return { status, frame, detections, lastFrameAt, fps, error, reconnect };
}

export default useCameraStream;
