import { apiClient } from "./axios";
import { WorkflowCreate, WorkflowDocument, WorkflowShort, WorkflowUpdate } from "../types/workflow";

export const workflowsApi = {
  list: () => apiClient.get<WorkflowShort[]>("/api/workflows/").then((r) => r.data),
  get: (id: string) => apiClient.get<WorkflowDocument>(`/api/workflows/${id}`).then((r) => r.data),
  create: (data: WorkflowCreate) => apiClient.post<WorkflowDocument>("/api/workflows/", data).then((r) => r.data),
  update: (id: string, data: WorkflowUpdate) => apiClient.put<WorkflowDocument>(`/api/workflows/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/api/workflows/${id}`).then((r) => r.data),
};
