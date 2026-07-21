import apiClient from "./api";

/**
 * Assumed backend contract (adjust here if your routes differ):
 *   GET    /api/incidents                    -> [Incident]  (supports filters below)
 *   GET    /api/incidents/{id}                -> Incident
 *   POST   /api/incidents                     -> Incident   (mainly used by the detection pipeline,
 *                                                             kept here for manual/admin creation too)
 *   PUT    /api/incidents/{id}                -> Incident   (e.g. updating status: open/acknowledged/resolved)
 *   DELETE /api/incidents/{id}                -> 204
 *
 * Query params supported by list: skip, limit, status, severity, camera_id
 */

export async function getIncidents({
  skip = 0,
  limit = 100,
  status,
  severity,
  cameraId,
} = {}) {
  const { data } = await apiClient.get("/api/incidents", {
    params: {
      skip,
      limit,
      status,
      severity,
      camera_id: cameraId,
    },
  });
  return data;
}

export async function getIncident(id) {
  const { data } = await apiClient.get(`/api/incidents/${id}`);
  return data;
}

export async function createIncident(incident) {
  const { data } = await apiClient.post("/api/incidents", incident);
  return data;
}

export async function updateIncident(id, incident) {
  const { data } = await apiClient.put(`/api/incidents/${id}`, incident);
  return data;
}

export async function deleteIncident(id) {
  await apiClient.delete(`/api/incidents/${id}`);
  return id;
}

// Convenience helper used by the Incidents page's "Resolve" action.
export async function resolveIncident(id) {
  return updateIncident(id, { status: "resolved" });
}
