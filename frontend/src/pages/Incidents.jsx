import { AlertTriangle, Check, Trash2 } from "lucide-react";

import { useAppContent } from "../context/AppContent";

const STATUS_OPTIONS = ["open", "acknowledged", "resolved"];
const SEVERITY_OPTIONS = ["low", "medium", "high", "critical"];

const SEVERITY_STYLES = {
  critical: "bg-danger/10 text-danger",
  high: "bg-danger/10 text-danger",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-gray-100 text-gray-600",
};

const STATUS_STYLES = {
  open: "bg-danger/10 text-danger",
  acknowledged: "bg-amber-100 text-amber-700",
  resolved: "bg-green-100 text-green-700",
};

export default function Incidents() {
  const { incidents, cameras } = useAppContent();
  const { incidents: list, loading, error, filters, setFilters, resolve, removeIncident } =
    incidents;

  const updateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined, skip: 0 }));
  };

  const handleResolve = async (id) => {
    try {
      await resolve(id);
    } catch {
      // error surfaced via incidents.error
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this incident? This cannot be undone.")) return;
    try {
      await removeIncident(id);
    } catch {
      // error surfaced via incidents.error
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Incidents</h1>
        <p className="text-sm text-gray-500">
          PPE violations, hook/load safety events, and other flagged incidents
        </p>
      </div>

      <div className="card p-4 flex flex-wrap gap-3 items-end">
        <div>
          <label className="text-xs font-medium text-gray-600">Status</label>
          <select
            value={filters.status || ""}
            onChange={(e) => updateFilter("status", e.target.value)}
            className="mt-1 block rounded-lg border border-gray-200 text-sm px-3 py-2 outline-none focus:ring-2 focus:ring-primary/40"
          >
            <option value="">All</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-gray-600">Severity</label>
          <select
            value={filters.severity || ""}
            onChange={(e) => updateFilter("severity", e.target.value)}
            className="mt-1 block rounded-lg border border-gray-200 text-sm px-3 py-2 outline-none focus:ring-2 focus:ring-primary/40"
          >
            <option value="">All</option>
            {SEVERITY_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-gray-600">Camera</label>
          <select
            value={filters.cameraId || ""}
            onChange={(e) => updateFilter("cameraId", e.target.value)}
            className="mt-1 block rounded-lg border border-gray-200 text-sm px-3 py-2 outline-none focus:ring-2 focus:ring-primary/40"
          >
            <option value="">All</option>
            {cameras.cameras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name || `Camera #${c.id}`}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-danger/10 text-danger text-sm px-3 py-2">
          {error}
        </div>
      )}

      <div className="card overflow-hidden">
        {loading ? (
          <p className="text-sm text-gray-500 p-6">Loading incidents…</p>
        ) : list.length === 0 ? (
          <div className="flex flex-col items-center text-center py-10 gap-2">
            <AlertTriangle className="text-gray-300" size={28} />
            <p className="text-sm text-gray-500">
              No incidents match these filters.
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                <th className="px-4 py-3 font-medium">Incident</th>
                <th className="px-4 py-3 font-medium">Camera</th>
                <th className="px-4 py-3 font-medium">Severity</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Detected</th>
                <th className="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map((incident) => (
                <tr key={incident.id}>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {incident.title || incident.type || "Incident"}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {incident.camera_name || `#${incident.camera_id}`}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-medium px-2 py-1 rounded-full ${
                        SEVERITY_STYLES[incident.severity] ||
                        "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {incident.severity || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-medium px-2 py-1 rounded-full ${
                        STATUS_STYLES[incident.status] ||
                        "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {incident.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {incident.created_at
                      ? new Date(incident.created_at).toLocaleString()
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      {incident.status !== "resolved" && (
                        <button
                          onClick={() => handleResolve(incident.id)}
                          title="Mark resolved"
                          className="p-1.5 rounded-lg text-green-700 hover:bg-green-50 transition"
                        >
                          <Check size={16} />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(incident.id)}
                        title="Delete incident"
                        className="p-1.5 rounded-lg text-danger hover:bg-danger/10 transition"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
