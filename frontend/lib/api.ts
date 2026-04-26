/**
 * SportShield — API Client
 * Axios-based client with JWT auth interceptors
 */

import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ─── Request Interceptor — Attach JWT ──────────────────────

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("sportshield_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ─── Response Interceptor — Handle 401 ────────────────────

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("sportshield_token");
        localStorage.removeItem("sportshield_user");
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ─── Auth API ─────────────────────────────────────────────

export const authAPI = {
  register: (data: RegisterRequest) => api.post("/api/auth/register", data),
  login: (data: LoginRequest) => api.post("/api/auth/login", data),
  me: () => api.get("/api/auth/me"),
  seedDemo: () => api.post("/api/auth/demo/seed"),
};

// ─── Assets API ───────────────────────────────────────────

export const assetsAPI = {
  upload: (formData: FormData) =>
    api.post("/api/assets/upload", formData),
  list: (params?: Record<string, any>) => api.get("/api/assets/", { params }),
  get: (id: number) => api.get(`/api/assets/${id}`),
  delete: (id: number) => api.delete(`/api/assets/${id}`),
  stats: () => api.get("/api/assets/stats/summary"),
};

// ─── Detections API ───────────────────────────────────────

export const detectionsAPI = {
  list: (params?: Record<string, any>) => api.get("/api/detections/", { params }),
  get: (id: number) => api.get(`/api/detections/${id}`),
  update: (id: number, data: any) => api.patch(`/api/detections/${id}`, data),
  scan: (assetId: number) => api.post(`/api/detections/scan/${assetId}`),
  stats: () => api.get("/api/detections/stats/overview"),
  seedDemo: () => api.post("/api/detections/demo/seed"),
};

// ─── Enforcement API ──────────────────────────────────────

export const enforcementAPI = {
  listCases: (params?: Record<string, any>) => api.get("/api/enforcement/cases", { params }),
  createCase: (data: any) => api.post("/api/enforcement/cases", data),
  getNotice: (caseId: number) => api.get(`/api/enforcement/cases/${caseId}/notice`),
  sendNotice: (caseId: number) => api.post(`/api/enforcement/cases/${caseId}/send`),
  updateCase: (caseId: number, data: any) => api.patch(`/api/enforcement/cases/${caseId}`, data),
  stats: () => api.get("/api/enforcement/stats"),
};

// ─── Alerts API ───────────────────────────────────────────

export const alertsAPI = {
  list: (params?: Record<string, any>) => api.get("/api/alerts/", { params }),
  markRead: (id: number) => api.post(`/api/alerts/${id}/read`),
  markAllRead: () => api.post("/api/alerts/read-all"),
};

// ─── Reports API ──────────────────────────────────────────

export const reportsAPI = {
  summary: () => api.get("/api/reports/summary"),
  downloadDetectionsCSV: () =>
    api.get("/api/reports/csv/detections", { responseType: "blob" }),
  downloadAssetsCSV: () =>
    api.get("/api/reports/csv/assets", { responseType: "blob" }),
};

// ─── Types ────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  org_name?: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  role: string;
  org_id?: number;
  org_name?: string;
}

export interface Asset {
  id: number;
  filename: string;
  original_filename: string;
  file_type: "image" | "video";
  file_size: number;
  title?: string;
  sport_category?: string;
  status: "processing" | "protected" | "at_risk" | "violated";
  protection_level: string;
  detections_count: number;
  watermark_id?: string;
  created_at: string;
}

export interface Detection {
  id: number;
  asset_id: number;
  asset_title?: string;
  detection_url: string;
  platform?: string;
  domain?: string;
  country_code?: string;
  latitude?: number;
  longitude?: number;
  similarity_score: number;
  match_type?: string;
  severity: "low" | "medium" | "high" | "critical";
  status: string;
  detected_at: string;
}
