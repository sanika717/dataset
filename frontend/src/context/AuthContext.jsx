import { createContext, useContext, useEffect, useState } from "react";

import { tokenStorage } from "../services/api";
import {
  login as loginRequest,
  register as registerRequest,
  getCurrentUser,
  logout as clearToken,
} from "../services/authService";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true while we check for an existing session
  const [error, setError] = useState(null);

  // On first load, if a token exists, validate it against /api/auth/me
  // so a page refresh doesn't lose the session.
  useEffect(() => {
    const restoreSession = async () => {
      const token = tokenStorage.get();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        console.error("Session restore failed:", err);
        clearToken();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = async (credentials) => {
    setError(null);
    try {
      const loggedInUser = await loginRequest(credentials);
      setUser(loggedInUser);
      return loggedInUser;
    } catch (err) {
      const message =
        err.response?.data?.detail || "Invalid email or password.";
      setError(message);
      throw err;
    }
  };

  const register = async (details) => {
    setError(null);
    try {
      const newUser = await registerRequest(details);
      setUser(newUser);
      return newUser;
    } catch (err) {
      const message =
        err.response?.data?.detail || "Unable to create account.";
      setError(message);
      throw err;
    }
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        setError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
