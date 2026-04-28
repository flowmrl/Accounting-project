import type { AuthProvider } from "@refinedev/core";

const API = "/api/v1";

export const authProvider: AuthProvider = {
  login: async ({ username, password }) => {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);

    const res = await fetch(`${API}/auth/token`, {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      return { success: false, error: { name: "Erreur", message: "Identifiants incorrects" } };
    }

    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    return { success: true, redirectTo: "/" };
  },

  logout: async () => {
    localStorage.removeItem("token");
    return { success: true, redirectTo: "/login" };
  },

  check: async () => {
    const token = localStorage.getItem("token");
    return token ? { authenticated: true } : { authenticated: false, redirectTo: "/login" };
  },

  getPermissions: async () => null,
  getIdentity: async () => {
    const token = localStorage.getItem("token");
    if (!token) return null;
    return { name: "Comptable", avatar: undefined };
  },

  onError: async (error) => {
    if (error?.status === 401) return { logout: true };
    return { error };
  },
};
