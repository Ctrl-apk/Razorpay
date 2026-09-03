import axios from "axios";

const BASE_URL = (import.meta as unknown as { env: Record<string, string> }).env?.VITE_API_BASE_URL || "/api";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});
