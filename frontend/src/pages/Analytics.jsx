import { useMemo, useState } from "react";
import { BarChart3 } from "lucide-react";

import { useAppContent } from "../context/AppContent";

const SEVERITY_ORDER = ["critical", "high", "medium", "low"];
const SEVERITY_COLORS = {
  critical: "bg-danger",
  high: "bg-danger",
  medium: "bg-amber-500",
  low: "bg-gray-400",
};

function BarRow({ label, count, max, colorClass = "bg-primary" }) {
  const pct = max > 0 ? Math.max(4, Math.round((count / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-28 shrink-0 text-gray-600 capitalize">{label}</span>
      <div className="flex-1 h-2.5 rounded-full bg-gray-100 overflow-hidden">
        <div className={`h-full rounded-full ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-gray-500 tabular-nums">{count}</span>
    </div>
  );
}

export default function Analytics() {
  const { incidents, dashboard } = useAppContent();
  const { incidents: list } = incidents;

  const [range, setRange] = useState({ from: "", to: "" });
  const [remoteAnalytics, setRemoteAnalytics] = useState(null);
  const [fetching, setFetching] = useState(false);
  const [fetchError, setFetchError] = useState(null);

  const bySeverity = useMemo(() => {
    const counts = {};
    for (const s of SEVERITY_ORDER) counts[s] = 0;
    list.forEach((i) => {
      if (i.severity) counts[i.severity] = (counts[i.severity] || 0) + 1;
    });
    return counts;
  }, [list]);

  const byCamera = useMemo(() => {
    const counts = {};
    list.forEach((i) => {
      const key = i.camera_name || `Camera #${i.camera_id}`;
      counts[key] = (counts[key] || 0) + 1;
    });
    return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8);
  }, [list]);

  const maxSeverity = Math.max(1, ...Object.values(bySeverity));
  const maxCamera = Math.max(1, ...byCamera.map(([, c]) => c));

  const handleFetchRange = async (e) => {
    e.preventDefault();
    setFetching(true);
    setFetchError(null);
    try {
      const data = await dashboard.fetchAnalytics(range);
      setRemoteAnalytics(data);
    } catch (err) {
      setFetchError(
        err.response?.data?.detail || "Failed to load analytics for that range."
      );
    } finally {
      setFetching(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Analytics</h1>
        <p className="text-sm text-gray-500">
          Incident trends and breakdowns across cameras and severities
        </p>
      </div>

      <form
        onSubmit={handleFetchRange}
        className="card p-4 flex flex-wrap items-end gap-3"
      >
        <div>
          <label className="text-xs font-medium text-gray-600">From</label>
          <input
            type="date"
            value={range.from}
            onChange={(e) => setRange((r) => ({ ...r, from: e.target.value }))}
            className="mt-1 block rounded-lg border border-gray-200 text-sm px-3 py-2 outline-none focus:ring-2 focus:ring-primary/40"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-600">To</label>
          <input
            type="date"
            value={range.to}
            onChange={(e) => setRange((r) => ({ ...r, to: e.target.value }))}
            className="mt-1 block rounded-lg border border-gray-200 text-sm px-3 py-2 outline-none focus:ring-2 focus:ring-primary/40"
          />
        </div>
        <button
          type="submit"
          disabled={fetching}
          className="bg-primary text-white text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 transition disabled:opacity-50"
        >
          {fetching ? "Loading…" : "Run report"}
        </button>
      </form>

      {fetchError && (
        <div className="rounded-lg bg-danger/10 text-danger text-sm px-3 py-2">
          {fetchError}
        </div>
      )}

      {remoteAnalytics && (
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-gray-900 mb-2">
            Report results
          </h2>
          <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 overflow-x-auto">
            {JSON.stringify(remoteAnalytics, null, 2)}
          </pre>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-900">
            Incidents by severity
          </h2>
          {list.length === 0 ? (
            <p className="text-sm text-gray-500">No incident data yet.</p>
          ) : (
            SEVERITY_ORDER.map((sev) => (
              <BarRow
                key={sev}
                label={sev}
                count={bySeverity[sev]}
                max={maxSeverity}
                colorClass={SEVERITY_COLORS[sev]}
              />
            ))
          )}
        </div>

        <div className="card p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-900">
            Top cameras by incident count
          </h2>
          {byCamera.length === 0 ? (
            <div className="flex flex-col items-center text-center py-6 gap-2">
              <BarChart3 className="text-gray-300" size={24} />
              <p className="text-sm text-gray-500">No incident data yet.</p>
            </div>
          ) : (
            byCamera.map(([name, count]) => (
              <BarRow key={name} label={name} count={count} max={maxCamera} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
