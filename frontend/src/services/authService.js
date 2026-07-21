import apiClient, { tokenStorage } from "./api";

/**
 * Assumed backend contract (adjust paths here if yours differ):
 *   POST /api/auth/login    { email, password }  -> { access_token, user }
 *   POST /api/auth/register { name, email, password } -> { access_token, user }
 *   GET  /api/auth/me       (Bearer token)        -> user
 */

export async function login({ email, password }) {
  const { data } = await apiClient.post("/api/auth/login", { email, password });
  if (data.access_token) {
    tokenStorage.set(data.access_token);
  }
  return data.user ?? data;
}

export async function register({ name, email, password }) {
  const { data } = await apiClient.post("/api/auth/register", {
    name,
    email,
    password,
  });
  if (data.access_token) {
    tokenStorage.set(data.access_token);
  }
  return data.user ?? data;
}

export async function getCurrentUser() {
  const { data } = await apiClient.get("/api/auth/me");
  return data;
}

export function logout() {
  tokenStorage.clear();
}
