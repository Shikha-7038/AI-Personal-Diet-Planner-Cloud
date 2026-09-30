import { createContext, useContext, useEffect, useState } from "react";
import { api, auth } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshProfile = async () => {
    if (!auth.getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await api.getProfile());
    } catch {
      auth.clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshProfile();
  }, []);

  const login = async (email, password) => {
    const data = await api.login(email, password);
    auth.setToken(data.access_token);
    await refreshProfile();
  };

  const register = async (name, email, password) => {
    const data = await api.register(name, email, password);
    auth.setToken(data.access_token);
    await refreshProfile();
  };

  const logout = () => {
    auth.clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
