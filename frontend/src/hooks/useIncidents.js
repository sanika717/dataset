import { useCallback, useEffect, useState } from "react";

import {
  getIncidents,
  getIncident,
  createIncident,
  updateIncident,
  deleteIncident,
  resolveIncident,
} from "../services/incidentService";

/**
 * Owns the incident list + filters + CRUD state.
 *
 * Usage:
 *   const {
 *     incidents, loading, error, filters, setFilters,
 *     refresh, addIncident, editIncident, removeIncident, resolve,
 *   } = useIncidents({ status: "open" });
 */
export function useIncidents(initialFilters = {}) {
  const [filters, setFilters] = useState({
    skip: 0,
    limit: 100,
    status: undefined,
    severity: undefined,
    cameraId: undefined,
    ...initialFilters,
  });
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getIncidents(filters);
      setIncidents(data);
      return data;
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load incidents.");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const fetchIncident = useCallback(async (id) => {
    try {
      return await getIncident(id);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load incident.");
      throw err;
    }
  }, []);

  const addIncident = useCallback(async (incident) => {
    try {
      const created = await createIncident(incident);
      setIncidents((prev) => [created, ...prev]);
      return created;
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create incident.");
      throw err;
    }
  }, []);

  const editIncident = useCallback(async (id, incident) => {
    try {
      const updated = await updateIncident(id, incident);
      setIncidents((prev) => prev.map((i) => (i.id === id ? updated : i)));
      return updated;
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update incident.");
      throw err;
    }
  }, []);

  const removeIncident = useCallback(async (id) => {
    try {
      await deleteIncident(id);
      setIncidents((prev) => prev.filter((i) => i.id !== id));
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete incident.");
      throw err;
    }
  }, []);

  const resolve = useCallback(async (id) => {
    try {
      const updated = await resolveIncident(id);
      setIncidents((prev) => prev.map((i) => (i.id === id ? updated : i)));
      return updated;
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to resolve incident.");
      throw err;
    }
  }, []);

  return {
    incidents,
    loading,
    error,
    filters,
    setFilters,
    refresh,
    fetchIncident,
    addIncident,
    editIncident,
    removeIncident,
    resolve,
  };
}

export default useIncidents;
