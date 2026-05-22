import axios from "axios";
import { toast } from "sonner";

const BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15_000,
});

// Attach JWT token if present
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("arb_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("arb_token");
      window.location.href = "/";
    } else {
      const detail = error.response?.data?.detail || error.message || "API request failed";
      toast.error(`[ERR] ${detail}`);
    }
    return Promise.reject(error);
  }
);
