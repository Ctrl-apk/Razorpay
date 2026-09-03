import { apiClient } from "./client";

export const scenariosApi = {
  list: async (): Promise<{ scenarios: string[] }> => {
    const res = await apiClient.get("/v1/scenarios");
    return res.data;
  },

  run: async (scenarioName: string) => {
    const res = await apiClient.post(`/v1/scenarios/${scenarioName}/run`);
    return res.data;
  },
};
