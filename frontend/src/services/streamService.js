import { tokenStorage } from "./api";

/**
 * Assumed backend contract (adjust here if your routes differ — this is
 * unbuilt on the backend side as of Phase 5, per detection_service.py /
 * websocket_service.py both being empty stubs):
 *
 *   WS  /api/cameras/{id}/stream?token={jwt}
 *
 *   Browsers can't set custom headers on a WebSocket handshake, so the JWT
 *   travels as a query param instead of an Authorization header. The server
 *   should validate it the same way the REST auth dependency does and close
 *   the socket (e.g. code 4401) on failure.
 *
 *   Server -> client messages, one of:
 *     - text frame, JSON:
 *         {
 *           "type": "frame",
 *           "image": "data:image/jpeg;base64,...",   // annotated frame
 *           "detections": [                            // optional, already
 *             { "label": "no_hardhat", "severity": "high",
 *               "box": [x, y, w, h] }                  // normalized 0..1
 *           ],
 *           "timestamp": "2026-07-18T10:15:00Z"
 *         }
 *     - binary frame (raw JPEG bytes) — used if the server skips JSON
 *       envelopes for lower latency; detections would arrive as a separate
 *       JSON text message in that mode.
 *
 *   Client -> server: nothing required; the socket is receive-only from the
 *   frontend's point of view.
 */

function wsBaseUrl() {
  const httpBase =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
  return httpBase.replace(/^http/, "ws").replace(/\/$/, "");
}

export function getCameraStreamUrl(cameraId) {
  const token = tokenStorage.get();
  const params = new URLSearchParams();
  if (token) params.set("token", token);
  return `${wsBaseUrl()}/api/cameras/${cameraId}/stream?${params.toString()}`;
}

export default { getCameraStreamUrl };
