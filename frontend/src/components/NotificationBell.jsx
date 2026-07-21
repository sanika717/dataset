import { useEffect, useRef, useState } from "react";
import { Bell, Check, Trash2, WifiOff } from "lucide-react";
import { Link } from "react-router-dom";

import { useAppContent } from "../context/AppContent";

const SEVERITY_DOT = {
  critical: "bg-danger",
  high: "bg-danger",
  medium: "bg-amber-500",
  low: "bg-gray-400",
};

function timeAgo(dateStr) {
  if (!dateStr) return "";
  const diffMs = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

/**
 * Self-contained bell + dropdown, backed by useAppContent().notifications
 * (real-time WebSocket with polling fallback — see useNotifications.js).
 * Drop it into your header/navbar, e.g.:
 *
 *   <nav>...<NotificationBell />...</nav>
 */
export default function NotificationBell() {
  const { notifications } = useAppContent();
  const { notifications: list, unreadCount, realtimeStatus, markRead, markAllRead, remove } =
    notifications;

  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleItemClick = (n) => {
    if (!n.read) markRead(n.id);
  };

  const isLive = realtimeStatus === "live";

  return (
    <div className="relative" ref={containerRef}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="relative p-2 rounded-lg hover:bg-gray-100 transition"
        aria-label="Notifications"
      >
        <Bell size={20} className="text-gray-600" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 rounded-full bg-danger text-white text-[10px] font-semibold flex items-center justify-center">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 max-h-[28rem] overflow-hidden flex flex-col card shadow-lg z-50">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <div className="flex items-center gap-1.5">
              <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
              {!isLive && (
                <span title="Live updates unavailable — polling instead">
                  <WifiOff size={12} className="text-gray-400" />
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={markAllRead}
                className="text-xs font-medium text-primary hover:underline"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="overflow-y-auto flex-1">
            {list.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">
                You're all caught up.
              </p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {list.map((n) => (
                  <li
                    key={n.id}
                    onClick={() => handleItemClick(n)}
                    className={`px-4 py-3 flex gap-2.5 cursor-pointer hover:bg-gray-50 transition ${
                      n.read ? "" : "bg-primary/5"
                    }`}
                  >
                    <span
                      className={`mt-1.5 h-1.5 w-1.5 rounded-full shrink-0 ${
                        SEVERITY_DOT[n.severity] || "bg-primary"
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 leading-snug">
                        {n.title || n.message}
                      </p>
                      {n.title && n.message && (
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                          {n.message}
                        </p>
                      )}
                      <p className="text-[11px] text-gray-400 mt-1">
                        {timeAgo(n.created_at)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        remove(n.id);
                      }}
                      className="text-gray-300 hover:text-danger transition shrink-0"
                      title="Dismiss"
                    >
                      <Trash2 size={14} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="px-4 py-2 border-t border-gray-100">
            <Link
              to="/incidents"
              onClick={() => setOpen(false)}
              className="flex items-center justify-center gap-1 text-xs font-medium text-primary py-1"
            >
              <Check size={12} />
              View all incidents
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
