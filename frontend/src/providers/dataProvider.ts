import simpleRestDataProvider from "@refinedev/simple-rest";

const API_URL = "/api/v1";

// Intercepte chaque requête pour ajouter le Bearer token
const httpClient = {
  async get(url: string, config?: RequestInit) {
    const token = localStorage.getItem("token");
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(url, { ...config, headers });
    if (!res.ok) throw { status: res.status, message: await res.text() };
    return { data: await res.json() };
  },
};

export const dataProvider = simpleRestDataProvider(API_URL);
