import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { workflowsApi } from "../api/workflows";
import { aiApi } from "../api/ai";
import { WorkflowCreate, WorkflowUpdate } from "../types/workflow";
import { useWorkflowStore } from "../store/workflowStore";
import { toast } from "sonner";

export const QUERY_KEYS = {
  workflows: ["workflows"] as const,
  workflow: (id: string) => ["workflows", id] as const,
};

export function useWorkflowList() {
  return useQuery({ queryKey: QUERY_KEYS.workflows, queryFn: workflowsApi.list });
}

export function useWorkflow(id: string | null) {
  return useQuery({
    queryKey: id ? QUERY_KEYS.workflow(id) : ["workflows", "null"],
    queryFn: () => workflowsApi.get(id!),
    enabled: !!id,
    onError: (error) => {
      toast.error(String(error));
    },
  });
}

export function useCreateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: WorkflowCreate) => workflowsApi.create(data),
    onSuccess: (wf) => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.workflows });
      useWorkflowStore.getState().loadWorkflow(wf._id, wf.name, wf.nodes, wf.edges);
      toast.success("Workflow saved.");
    },
    onError: (error) => {
      toast.error(String(error));
    },
  });
}

export function useUpdateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkflowUpdate }) => workflowsApi.update(id, data),
    onSuccess: (wf) => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.workflows });
      useWorkflowStore.getState().loadWorkflow(wf._id, wf.name, wf.nodes, wf.edges);
      toast.success("Workflow updated.");
    },
    onError: (error) => {
      toast.error(String(error));
    },
  });
}

export function useDeleteWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workflowsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.workflows });
      useWorkflowStore.getState().newWorkflow();
      toast.success("Workflow deleted.");
    },
    onError: (error) => {
      toast.error(String(error));
    },
  });
}

export function useGenerateWorkflow() {
  const store = useWorkflowStore.getState();
  return useMutation({
    mutationFn: (prompt: string) => aiApi.generate(prompt),
    onSuccess: (data) => {
      store.setNodes(data.nodes);
      store.setEdges(data.edges);
      toast.success("AI workflow generated.");
    },
    onError: (error) => {
      toast.error(String(error));
    },
  });
}
