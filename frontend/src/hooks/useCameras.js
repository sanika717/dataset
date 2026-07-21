import { useCallback, useEffect, useState } from "react";

import {
  getCameras,
  getCamera,
  createCamera,
  updateCamera,
  deleteCamera,
} from "../services/cameraService";

/**
 * Owns the camera list + CRUD state so pages/components don't each
 * have to duplicate loading/error handling around cameraService.
 *
 * Usage:
 *   const { cameras, loading, error, refresh, addCamera, editCamera, removeCamera } = useCameras();
 */
export function useCameras({ skip = 0, limit = 100, autoLoad = true } = {}) {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(autoLoad);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCameras({ skip, limit });
      setCameras(data);
      return data;
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load cameras.");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [skip, limit]);

  useEffect(() => {
    if (autoLoad) {
      refresh();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoLoad, skip, limit]);

  const fetchCamera = useCallback(async (id) => {
    try {
      return await getCamera(id);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load camera.");
      throw err;
    }
  }, []);

  const addCamera = useCallback(async (camera) => {
    try {
      const created = await createCamera(camera);
      setCameras((prev) => [...prev, created]);
      return created;
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create camera.");
      throw err;
    }
  }, []);

  const editCamera = useCallback(async (id, camera) => {
    try {
      const updated = await updateCamera(id, camera);
      setCameras((prev) => prev.map((c) => (c.id === id ? updated : c)));
      return updated;
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update camera.");
      throw err;
    }
  }, []);

  const removeCamera = useCallback(async (id) => {
    try {
      await deleteCamera(id);
      setCameras((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete camera.");
      throw err;
    }
  }, []);

  return {
    cameras,
    loading,
    error,
    refresh,
    fetchCamera,
    addCamera,
    editCamera,
    removeCamera,
  };
}

export default useCameras;
