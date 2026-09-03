import { apiClient } from "./client";
import type { Incident, Investigation } from "../types";

export const incidentsApi = {
  list: async (params?: { service?: string; status?: string }): Promise<Incident[]> => {
    const res = await apiClient.get("/v1/incidents", { params });
    return res.data;
  },

  get: async (incidentId: string): Promise<Incident> => {
    const res = await apiClient.get(`/v1/incidents/${incidentId}`);
    return res.data;
  },

  getInvestigation: async (incidentId: string): Promise<Investigation> => {
    const res = await apiClient.get(`/v1/incidents/${incidentId}/investigation`);
    return res.data;
  },

  triggerInvestigation: async (incidentId: string) => {
    const res = await apiClient.post(`/v1/incidents/${incidentId}/investigate`);
    return res.data;
  },

  getTimeline: async (incidentId: string) => {
    const res = await apiClient.get(`/v1/incidents/${incidentId}/timeline`);
    return res.data;
  },

  getEvidence: async (incidentId: string) => {
    const res = await apiClient.get(`/v1/incidents/${incidentId}/evidence`);
    return res.data;
  },

  resolve: async (incidentId: string) => {
    const res = await apiClient.patch(`/v1/incidents/${incidentId}/resolve`);
    return res.data;
  },

  // Returns null instead of throwing when no investigation exists yet
  getInvestigationSafe: async (incidentId: string): Promise<import("../types").Investigation | null> => {
    try {
      const res = await apiClient.get(`/v1/incidents/${incidentId}/investigation`);
      return res.data;
    } catch {
      return null;
    }
  },
};
