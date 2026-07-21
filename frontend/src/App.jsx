import { Routes, Route, Navigate } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Incidents from "./pages/Incidents";
import Camera from "./pages/Camera";
import Analytics from "./pages/Analytics";
import Login from "./pages/Login";
import Register from "./pages/Register";

import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

// NOTE: Workers and Reports routes were dropped along with the old
// Workers/Alerts/Reports schema — Incidents replaces Alerts + Workers,
// Analytics replaces Reports. Settings wasn't part of this rewiring pass;
// re-add its <Route> here once its page is rebuilt against the new schema.
function Protected({ children }) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  );
}

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Everything else requires an authenticated session */}
      <Route
        path="/"
        element={
          <Protected>
            <Dashboard />
          </Protected>
        }
      />

      <Route
        path="/incidents"
        element={
          <Protected>
            <Incidents />
          </Protected>
        }
      />

      <Route
        path="/cameras"
        element={
          <Protected>
            <Camera />
          </Protected>
        }
      />

      <Route
        path="/analytics"
        element={
          <Protected>
            <Analytics />
          </Protected>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
