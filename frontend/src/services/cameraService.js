import apiClient from "./api";

/**
 * Assumed backend contract (adjust here if your routes differ):
 *   GET    /api/cameras            -> [Camera]
 *   GET    /api/cameras/{id}       -> Camera
 *   POST   /api/cameras            -> Camera
 *   PUT    /api/cameras/{id}       -> Camera
 *   DELETE /api/cameras/{id}       -> 204
 */

export async function getCameras({ skip = 0, limit = 100 } = {}) {
  const { data } = await apiClient.get("/api/cameras", {
    params: { skip, limit },
  });
  return data;
}

export async function getCamera(id) {
  const { data } = await apiClient.get(`/api/cameras/${id}`);
  return data;
}

export async function createCamera(camera) {
  const { data } = await apiClient.post("/api/cameras", camera);
  return data;
}

export async function updateCamera(id, camera) {
  const { data } = await apiClient.put(`/api/cameras/${id}`, camera);
  return data;
}

export async function deleteCamera(id) {
  await apiClient.delete(`/api/cameras/${id}`);
  return id;
}
