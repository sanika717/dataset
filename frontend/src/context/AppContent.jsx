import { createContext, useContext } from "react";

import { useCameras } from "../hooks/useCameras";
import { useIncidents } from "../hooks/useIncidents";
import { useNotifications } from "../hooks/useNotifications";
import { useDashboard } from "../hooks/useDashboard";

/**
 * App-wide data layer for the new Users/Cameras/Incidents/Notifications
 * schema. Replaces the old Workers/Alerts/Reports state this context used
 * to hold — pages should pull from here (or from the individual hooks
 * directly) instead of managing their own fetch/loading/error state.
 *
 * Mounted once in main.jsx, inside AuthProvider and above <App />, so
 * every route has access via useAppContent().
 */
const AppContext = createContext(null);

export function AppProvider({ children }) {
  const camerasState = useCameras();
  const incidentsState = useIncidents();
  const notificationsState = useNotifications({ realtime: true });
  const dashboardState = useDashboard();

  const value = {
    cameras: camerasState,
    incidents: incidentsState,
    notifications: notificationsState,
    dashboard: dashboardState,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContent() {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error("useAppContent must be used within an AppProvider");
  }
  return ctx;
}

export default AppContext;
