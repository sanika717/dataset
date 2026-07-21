import { Link } from "react-router-dom";
import {
  Camera as CameraIcon,
  AlertTriangle,
  Bell,
  Activity,
  RefreshCw,
} from "lucide-react";

import { useAppContent } from "../context/AppContent";

const SEVERITY_STYLES = {
  critical: "bg-danger/10 text-danger",
  high: "bg-danger/10 text-danger",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-gray-100 text-gray-600",
};

// Tailwind needs full, static class names to pick up at build time — no
// `bg-${accent}/10` string interpolation — so accents are mapped explicitly.
const ACCENT_STYLES = {
  primary: { bg: "bg-primary/10", text: "text-primary" },
  danger: { bg: "bg-danger/10", text: "text-danger" },
};

function StatCard({ icon: Icon, label, value, loading, accent = "primary" }) {
  const { bg, text } = ACCENT_STYLES[accent] || ACCENT_STYLES.primary;
  return (
    <div className="card flex items-center gap-4 p-4">
      <div className={`h-11 w-11 rounded-xl ${bg} flex items-center justify-center shrink-0`}>
        <Icon className={text} size={20} />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-xl font-semibold text-gray-900">
          {loading ? "—" : value}
        </p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { dashboard, incidents, cameras, notifications } = useAppContent();

  const stats = dashboard.stats || {};
  const recentIncidents = [...(incidents.incidents || [])]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  const handleRefresh = () => {
    dashboard.refresh();
    incidents.refresh();
    cameras.refresh();
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500">
            Live overview of site cameras, incidents, and alerts
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1.5 text-sm text-gray-600 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-gray-50 transition"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {dashboard.error && (
        <div className="rounded-lg bg-danger/10 text-danger text-sm px-3 py-2">
          {dashboard.error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={CameraIcon}
          label="Active cameras"
          value={
            stats.active_cameras ??
            cameras.cameras.filter((c) => c.is_active !== false).length
          }
          loading={dashboard.loading && cameras.loading}
        />
        <StatCard
          icon={AlertTriangle}
          label="Open incidents"
          value={
            stats.open_incidents ??
            incidents.incidents.filter((i) => i.status !== "resolved").length
          }
          loading={dashboard.loading && incidents.loading}
          accent="danger"
        />
        <StatCard
          icon={Activity}
          label="Incidents today"
          value={stats.incidents_today ?? "—"}
          loading={dashboard.loading}
        />
        <StatCard
          icon={Bell}
          label="Unread notifications"
          value={notifications.unreadCount}
          loading={notifications.loading}
        />
      </div>

      <div className="card p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-900">
            Recent incidents
          </h2>
          <Link to="/incidents" className="text-sm text-primary font-medium">
            View all
          </Link>
        </div>

        {incidents.loading ? (
          <p className="text-sm text-gray-500 py-4">Loading incidents…</p>
        ) : recentIncidents.length === 0 ? (
          <p className="text-sm text-gray-500 py-4">
            No incidents recorded yet.
          </p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {recentIncidents.map((incident) => (
              <li
                key={incident.id}
                className="py-3 flex items-center justify-between gap-4"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {incident.title || incident.type || "Incident"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {incident.camera_name ||
                      `Camera #${incident.camera_id}`}{" "}
                    · {new Date(incident.created_at).toLocaleString()}
                  </p>
                </div>
                <span
                  className={`text-xs font-medium px-2 py-1 rounded-full ${
                    SEVERITY_STYLES[incident.severity] ||
                    "bg-gray-100 text-gray-600"
                  }`}
                >
                  {incident.severity || incident.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
