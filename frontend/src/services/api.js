/**
 * Thin wrapper around fetch() for the backend REST API.
 * Adds the JWT (from localStorage) to every authenticated request and
 * throws a normal Error with the backend's message on non-2xx responses.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "diet_planner_token";

export const auth = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (t) => localStorage.setItem(TOKEN_KEY, t),
  clearToken: () => localStorage.removeItem(TOKEN_KEY),
};

async function request(path, { method = "GET", body, isForm = false } = {}) {
  const headers = {};
  const token = auth.getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (!isForm && body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return null;

  let data = null;
  try {
    data = await res.json();
  } catch {
    /* empty body is fine for some responses */
  }

  if (!res.ok) {
    const message = (data && data.detail) || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

export const api = {
  register: (name, email, password) => request("/register", { method: "POST", body: { name, email, password } }),
  login: (email, password) => request("/login", { method: "POST", body: { email, password } }),
  getProfile: () => request("/profile"),
  updateProfile: (fields) => request("/profile", { method: "PUT", body: fields }),
  generatePlan: (save = true) => request("/generate-plan", { method: "POST", body: { save } }),
  listPlans: () => request("/plans"),
  getPlan: (id) => request(`/plans/${id}`),
  deletePlan: (id) => request(`/plans/${id}`, { method: "DELETE" }),
  uploadFile: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/upload", { method: "POST", body: form, isForm: true });
  },
  listFiles: () => request("/files"),
  deleteFile: (id) => request(`/files/${id}`, { method: "DELETE" }),
};
