import { useEffect, useRef } from "react";
import { RefreshCw, WifiOff } from "lucide-react";

import { useCameraStream } from "../hooks/useCameraStream";

const STATUS_META = {
  idle: { label: "Idle", dot: "bg-gray-300", text: "text-gray-500" },
  connecting: { label: "Connecting…", dot: "bg-amber-400 animate-pulse", text: "text-amber-600" },
  live: { label: "Live", dot: "bg-green-500 animate-pulse", text: "text-green-700" },
  reconnecting: { label: "Reconnecting…", dot: "bg-amber-400 animate-pulse", text: "text-amber-600" },
  error: { label: "Error", dot: "bg-danger", text: "text-danger" },
  closed: { label: "Offline", dot: "bg-gray-300", text: "text-gray-500" },
};

const SEVERITY_COLOR = {
  critical: "#dc2626",
  high: "#dc2626",
  medium: "#d97706",
  low: "#6b7280",
};

/**
 * Renders one camera's live stream on a canvas, drawing any detection
 * boxes the server sends alongside each frame. `enabled` lets a parent
 * (e.g. a grid of camera tiles) suspend the WebSocket for feeds that are
 * scrolled out of view instead of running every stream at once.
 */
export default function LiveStream({
  cameraId,
  cameraName,
  enabled = true,
  aspectRatio = "16 / 9",
}) {
  const { status, frame, detections, fps, error, reconnect } = useCameraStream(
    cameraId,
    { enabled }
  );
  const canvasRef = useRef(null);
  const imgRef = useRef(null);

  useEffect(() => {
    if (!frame) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const img = imgRef.current || new Image();
    imgRef.current = img;

    img.onload = () => {
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      ctx.drawImage(img, 0, 0);

      detections.forEach((d) => {
        if (!d.box || d.box.length !== 4) return;
        const [x, y, w, h] = d.box;
        const px = x * canvas.width;
        const py = y * canvas.height;
        const pw = w * canvas.width;
        const ph = h * canvas.height;
        const color = SEVERITY_COLOR[d.severity] || "#2563eb";

        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(px, py, pw, ph);

        if (d.label) {
          ctx.font = "12px sans-serif";
          const textWidth = ctx.measureText(d.label).width;
          ctx.fillStyle = color;
          ctx.fillRect(px, Math.max(0, py - 16), textWidth + 8, 16);
          ctx.fillStyle = "#fff";
          ctx.fillText(d.label, px + 4, Math.max(12, py - 4));
        }
      });
    };
    img.src = frame;
  }, [frame, detections]);

  const meta = STATUS_META[status] || STATUS_META.idle;
  const isDown = status === "error" || status === "closed";

  return (
    <div
      className="relative w-full rounded-xl overflow-hidden bg-gray-900"
      style={{ aspectRatio }}
    >
      <canvas ref={canvasRef} className="w-full h-full object-contain" />

      {(!frame || isDown) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-gray-400">
          {isDown ? <WifiOff size={22} /> : null}
          <span className="text-xs">
            {isDown ? error || "Stream unavailable" : "Waiting for frames…"}
          </span>
          {isDown && (
            <button
              onClick={reconnect}
              className="flex items-center gap-1 text-xs font-medium text-white bg-white/10 rounded-lg px-2.5 py-1.5 hover:bg-white/20 transition"
            >
              <RefreshCw size={12} />
              Retry
            </button>
          )}
        </div>
      )}

      <div className="absolute top-2 left-2 flex items-center gap-1.5 bg-black/50 rounded-full px-2 py-1">
        <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
        <span className="text-[11px] font-medium text-white">{meta.label}</span>
      </div>

      {cameraName && (
        <div className="absolute bottom-2 left-2 bg-black/50 rounded-lg px-2 py-1">
          <span className="text-[11px] font-medium text-white">{cameraName}</span>
        </div>
      )}

      {status === "live" && (
        <div className="absolute bottom-2 right-2 bg-black/50 rounded-lg px-2 py-1">
          <span className="text-[11px] text-gray-200 tabular-nums">{fps} fps</span>
        </div>
      )}
    </div>
  );
}
