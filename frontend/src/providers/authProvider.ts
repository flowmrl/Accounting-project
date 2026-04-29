import type { AuthProvider } from "@refinedev/core";

const API = "/api/v1";

export const authProvider: AuthProvider = {
  login: async ({ email, password }) => {
    // OAuth2 password flow expects `username` field
    const form = new URLSearchParams();
    form.append("username", email ?? "");
    form.append("password", password ?? "");

    const res = await fetch(`${API}/auth/token`, {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      return { success: false, error: { name: "Erreur", message: "Identifiants incorrects" } };
    }

    const data = await res.json();
    localStorage.setItem("token", data.access_token);

    // Fetch identity to cache name
    const meRes = await fetch(`${API}/auth/me`, {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });
    if (meRes.ok) {
      const me = await meRes.json();
      localStorage.setItem("user", JSON.stringify(me));
    }

    return { success: true, redirectTo: "/" };
  },

  logout: async () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    return { success: true, redirectTo: "/login" };
  },

  check: async () => {
    const token = localStorage.getItem("token");
    return token ? { authenticated: true } : { authenticated: false, redirectTo: "/login" };
  },

  getPermissions: async () => {
    const raw = localStorage.getItem("user");
    if (!raw) return null;
    const user = JSON.parse(raw);
    return user.is_superadmin ? "superadmin" : "user";
  },

  getIdentity: async () => {
    const raw = localStorage.getItem("user");
    if (raw) {
      const user = JSON.parse(raw);
      return { name: user.full_name, email: user.email, avatar: undefined };
    }
    return { name: "Utilisateur", avatar: undefined };
  },

  onError: async (error) => {
    if (error?.status === 401) return { logout: true };
    return { error };
  },
};
