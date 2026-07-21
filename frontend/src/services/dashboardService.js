import apiClient from "./api";

/**
 * Assumed backend contract (adjust here if your routes differ):
 *   GET /api/dashboard  -> live-computed summary stats (never cached in DB)
 *   GET /api/analytics  -> time-series / breakdown data for charts (Phase 4 - Analytics page)
 */

export async function getDashboardStats() {
  const { data } = await apiClient.get("/api/dashboard");
  return data;
}

export async function getAnalytics({ from, to } = {}) {
  const { data } = await apiClient.get("/api/analytics", {
    params: { from, to },
  });
  return data;
}
