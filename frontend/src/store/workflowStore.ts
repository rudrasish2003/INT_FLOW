import { create } from "zustand";
import { WorkflowEdge, WorkflowNode } from "../types/workflow";
import {
  applyEdgeChanges,
  applyNodeChanges,
  addEdge,
  Connection,
  EdgeChange,
  NodeChange,
} from "@xyflow/react";

interface WorkflowState {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  selectedNodeId: string | null;
  activeWorkflowId: string | null;
  activeWorkflowName: string;
  isDirty: boolean;
  setNodes: (nodes: WorkflowNode[]) => void;
  setEdges: (edges: WorkflowEdge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  selectNode: (id: string | null) => void;
  updateNodeData: (id: string, data: Partial<WorkflowNode["data"]>) => void;
  loadWorkflow: (id: string, name: string, nodes: WorkflowNode[], edges: WorkflowEdge[]) => void;
  newWorkflow: () => void;
  setActiveWorkflowName: (name: string) => void;
  markDirty: () => void;
}

let edgeCounter = 1;

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  activeWorkflowId: null,
  activeWorkflowName: "Untitled Workflow",
  isDirty: false,

  setNodes: (nodes) => set({ nodes, isDirty: true }),
  setEdges: (edges) => set({ edges, isDirty: true }),

  onNodesChange: (changes) =>
    set((s) => ({
      nodes: applyNodeChanges(changes, s.nodes as any) as WorkflowNode[],
      isDirty: true,
    })),

  onEdgesChange: (changes) =>
    set((s) => ({
      edges: applyEdgeChanges(changes, s.edges as any) as WorkflowEdge[],
      isDirty: true,
    })),

  onConnect: (connection) =>
    set((s) => {
      const newEdge: WorkflowEdge = {
        ...connection,
        id: `e${edgeCounter++}`,
        sourceHandle: (connection.sourceHandle as any) ?? "out",
      };
      return {
        edges: addEdge(newEdge as any, s.edges as any) as WorkflowEdge[],
        isDirty: true,
      };
    }),

  selectNode: (id) => set({ selectedNodeId: id }),

  updateNodeData: (id, data) =>
    set((s) => ({
      nodes: s.nodes.map((node) =>
        node.id === id ? { ...node, data: { ...node.data, ...data } } : node
      ),
      isDirty: true,
    })),

  loadWorkflow: (id, name, nodes, edges) =>
    set({ activeWorkflowId: id, activeWorkflowName: name, nodes, edges, isDirty: false, selectedNodeId: null }),

  newWorkflow: () =>
    set({
      activeWorkflowId: null,
      activeWorkflowName: "Untitled Workflow",
      nodes: [],
      edges: [],
      isDirty: false,
      selectedNodeId: null,
    }),

  setActiveWorkflowName: (name) => set({ activeWorkflowName: name }),
  markDirty: () => set({ isDirty: true }),
}));
