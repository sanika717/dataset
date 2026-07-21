import { useCallback, useEffect, useState } from "react";

import { getDashboardStats, getAnalytics } from "../services/dashboardService";

/**
 * Owns live dashboard summary stats (never cached in DB — recomputed
 * server-side on each call) plus on-demand analytics fetches for the
 * Analytics page (Phase 4).
 *
 * Usage:
 *   const { stats, loading, error, refresh, fetchAnalytics } =
 *     useDashboard({ pollIntervalMs: 15000 });
 */
export function useDashboard({ pollIntervalMs = 0 } = {}) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDashboardStats();
      setStats(data);
      return data;
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load dashboard stats.");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!pollIntervalMs) return undefined;
    const id = setInterval(refresh, pollIntervalMs);
    return () => clearInterval(id);
  }, [pollIntervalMs, refresh]);

  const fetchAnalytics = useCallback(async ({ from, to } = {}) => {
    try {
      return await getAnalytics({ from, to });
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load analytics.");
      throw err;
    }
  }, []);

  return { stats, loading, error, refresh, fetchAnalytics };
}

export default useDashboard;
