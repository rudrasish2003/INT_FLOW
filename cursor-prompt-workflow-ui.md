# Cursor Prompt — Workflow Builder UI (React + ReactFlow)

## Project Overview

Build a full-featured n8n-style visual workflow builder frontend in React that integrates with an existing FastAPI backend. The UI must allow users to create, edit, save, and AI-generate workflows made of nodes and edges on an interactive canvas.

---

## Tech Stack

- **React 18** with **TypeScript**
- **Vite** as the build tool
- **ReactFlow** (`@xyflow/react`) for the canvas
- **Zustand** for global state management
- **TanStack Query** (`@tanstack/react-query`) for all API calls
- **Axios** for HTTP requests
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components (Dialog, Button, Input, Select, Textarea, Toast)
- **React Hook Form** + **Zod** for form validation

Install all dependencies:
```bash
npm create vite@latest workflow-builder -- --template react-ts
cd workflow-builder
npm install @xyflow/react zustand @tanstack/react-query axios tailwindcss @hookform/resolvers zod react-hook-form
npx shadcn@latest init
npx shadcn@latest add button input select textarea dialog label toast badge
```

---

## Backend API Reference

**Base URL:** `http://localhost:8000`

**CORS:** Already configured for `http://localhost:5173`

### Endpoints

#### Workflows

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/api/workflows/` | — | `WorkflowShort[]` |
| POST | `/api/workflows/` | `WorkflowCreate` | `WorkflowDocument` |
| GET | `/api/workflows/:id` | — | `WorkflowDocument` |
| PUT | `/api/workflows/:id` | `WorkflowUpdate` | `WorkflowDocument` |
| DELETE | `/api/workflows/:id` | — | `{ deleted: true }` |

#### AI Generation

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/api/ai/generate` | `{ prompt: string }` | `{ nodes: Node[], edges: Edge[] }` |

#### Health

| Method | Path | Response |
|--------|------|----------|
| GET | `/health/` | `{ status: "ok", database: "connected" \| "error" }` |

---

## TypeScript Types

Create `src/types/workflow.ts` with exactly these types — they mirror the backend schemas:

```typescript
export type NodeType = "start" | "api" | "condition" | "startNode" | "apiNode" | "conditionNode";

export interface Position {
  x: number;
  y: number;
}

export interface NodeData {
  label: string;
  url?: string;
  method?: "GET" | "POST" | "PUT" | "DELETE";
  headers?: Record<string, string>;
  body?: Record<string, unknown>;
  condition?: string;
}

export interface WorkflowNode {
  id: string;
  type: NodeType;
  position: Position;
  data: NodeData;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  sourceHandle?: "out" | "true" | "false" | null;
  target: string;
  label?: string;
}

export interface WorkflowDocument {
  _id: string;
  name: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  created_at: string;
  updated_at: string;
}

export interface WorkflowShort {
  id: string;
  name: string;
  updated_at: string;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface WorkflowUpdate extends WorkflowCreate {}
```

---

## File Structure

```
src/
├── api/
│   ├── axios.ts           # Axios instance with base URL
│   ├── workflows.ts       # All workflow API functions
│   └── ai.ts             # AI generate API function
├── types/
│   └── workflow.ts        # All TypeScript types (above)
├── store/
│   └── workflowStore.ts   # Zustand store
├── components/
│   ├── nodes/
│   │   ├── StartNode.tsx
│   │   ├── ApiNode.tsx
│   │   └── ConditionNode.tsx
│   ├── edges/
│   │   └── CustomEdge.tsx
│   ├── panels/
│   │   ├── Sidebar.tsx        # Left panel: workflow list
│   │   ├── Toolbar.tsx        # Top bar: add node buttons, save, AI generate
│   │   └── NodeEditPanel.tsx  # Right panel: node detail editor
│   └── modals/
│       ├── SaveWorkflowModal.tsx
│       └── AIGenerateModal.tsx
├── hooks/
│   ├── useWorkflows.ts        # TanStack Query hooks
│   └── useWorkflowCanvas.ts   # ReactFlow helpers
├── pages/
│   └── WorkflowEditor.tsx     # Main page
└── main.tsx
```

---

## API Layer

### `src/api/axios.ts`
```typescript
import axios from "axios";

export const apiClient = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});
```

### `src/api/workflows.ts`
```typescript
import { apiClient } from "./axios";
import { WorkflowCreate, WorkflowDocument, WorkflowShort, WorkflowUpdate } from "../types/workflow";

export const workflowsApi = {
  list: () => apiClient.get<WorkflowShort[]>("/api/workflows/").then(r => r.data),
  get: (id: string) => apiClient.get<WorkflowDocument>(`/api/workflows/${id}`).then(r => r.data),
  create: (data: WorkflowCreate) => apiClient.post<WorkflowDocument>("/api/workflows/", data).then(r => r.data),
  update: (id: string, data: WorkflowUpdate) => apiClient.put<WorkflowDocument>(`/api/workflows/${id}`, data).then(r => r.data),
  delete: (id: string) => apiClient.delete(`/api/workflows/${id}`).then(r => r.data),
};
```

### `src/api/ai.ts`
```typescript
import { apiClient } from "./axios";
import { WorkflowNode, WorkflowEdge } from "../types/workflow";

export const aiApi = {
  generate: (prompt: string) =>
    apiClient
      .post<{ nodes: WorkflowNode[]; edges: WorkflowEdge[] }>("/api/ai/generate", { prompt })
      .then(r => r.data),
};
```

---

## Zustand Store — `src/store/workflowStore.ts`

```typescript
import { create } from "zustand";
import { WorkflowNode, WorkflowEdge } from "../types/workflow";
import {
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange,
  Connection,
  addEdge,
} from "@xyflow/react";

interface WorkflowState {
  // Canvas state
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  selectedNodeId: string | null;
  activeWorkflowId: string | null;
  activeWorkflowName: string;
  isDirty: boolean;

  // Actions
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
      nodes: applyNodeChanges(changes, s.nodes as any) as unknown as WorkflowNode[],
      isDirty: true,
    })),

  onEdgesChange: (changes) =>
    set((s) => ({
      edges: applyEdgeChanges(changes, s.edges as any) as unknown as WorkflowEdge[],
      isDirty: true,
    })),

  onConnect: (connection) =>
    set((s) => {
      const newEdge = {
        ...connection,
        id: `e${edgeCounter++}`,
        sourceHandle: (connection.sourceHandle as any) ?? "out",
      };
      return {
        edges: addEdge(newEdge, s.edges as any) as unknown as WorkflowEdge[],
        isDirty: true,
      };
    }),

  selectNode: (id) => set({ selectedNodeId: id }),

  updateNodeData: (id, data) =>
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === id ? { ...n, data: { ...n.data, ...data } } : n
      ),
      isDirty: true,
    })),

  loadWorkflow: (id, name, nodes, edges) =>
    set({ activeWorkflowId: id, activeWorkflowName: name, nodes, edges, isDirty: false, selectedNodeId: null }),

  newWorkflow: () =>
    set({ activeWorkflowId: null, activeWorkflowName: "Untitled Workflow", nodes: [], edges: [], isDirty: false, selectedNodeId: null }),

  setActiveWorkflowName: (name) => set({ activeWorkflowName: name }),
  markDirty: () => set({ isDirty: true }),
}));
```

---

## Custom Node Components

### Node design rules
- All nodes use Tailwind, no inline styles
- Nodes have a colored top-left badge showing their type
- Show label prominently in the center
- API nodes show method + truncated URL below the label
- Condition nodes show the condition expression below the label
- Output handles: Start/API have one handle on the right (`id="out"`). Condition has two handles: bottom-right labeled **true** (green), far-right labeled **false** (red)
- Input handle on the left for all nodes except Start
- Clicking a node calls `selectNode(id)` to open the right panel

### `src/components/nodes/StartNode.tsx`
```tsx
import { Handle, Position, NodeProps } from "@xyflow/react";
import { useWorkflowStore } from "../../store/workflowStore";

export function StartNode({ id, data }: NodeProps) {
  const selectNode = useWorkflowStore(s => s.selectNode);
  return (
    <div
      onClick={() => selectNode(id)}
      className="w-44 rounded-xl border-2 border-emerald-500 bg-emerald-50 cursor-pointer hover:border-emerald-600 transition-colors"
    >
      <div className="px-3 py-2">
        <span className="text-[10px] font-bold text-emerald-700 bg-emerald-200 px-2 py-0.5 rounded">START</span>
        <p className="mt-1 text-sm font-medium text-emerald-900 truncate">{data.label as string}</p>
      </div>
      <Handle type="source" position={Position.Right} id="out" className="!w-3 !h-3 !bg-emerald-500" />
    </div>
  );
}
```

### `src/components/nodes/ApiNode.tsx`
Same pattern as StartNode but:
- Border/badge color: `blue-500` / `blue-50` / `blue-200` / `blue-900`
- Badge text: `API`
- Show `{data.method} {data.url}` truncated below label in `text-[10px] text-blue-600`
- Has both `Handle type="target"` on Left and `Handle type="source"` on Right with `id="out"`

### `src/components/nodes/ConditionNode.tsx`
Same pattern but:
- Border/badge color: `amber-500` / `amber-50` / `amber-200` / `amber-900`
- Badge text: `CONDITION`
- Show `data.condition` below label in `text-[10px] text-amber-600`
- Has `Handle type="target"` on Left
- Has `Handle type="source"` on Bottom with `id="true"` — label "true" in green text below handle
- Has `Handle type="source"` on Right with `id="false"` — label "false" in red text beside handle

---

## Custom Edge — `src/components/edges/CustomEdge.tsx`

```tsx
import { BaseEdge, EdgeLabelRenderer, getBezierPath, EdgeProps } from "@xyflow/react";

export function CustomEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data, sourceHandleId, label }: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
  
  const color = sourceHandleId === "true" ? "#1D9E75" : sourceHandleId === "false" ? "#E24B4A" : "#378ADD";

  return (
    <>
      <BaseEdge path={edgePath} style={{ stroke: color, strokeWidth: 2 }} />
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{ transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)` }}
            className="absolute text-[10px] bg-white border border-gray-200 px-1.5 py-0.5 rounded pointer-events-none"
          >
            {label as string}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
```

---

## TanStack Query Hooks — `src/hooks/useWorkflows.ts`

```typescript
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { workflowsApi } from "../api/workflows";
import { aiApi } from "../api/ai";
import { WorkflowCreate, WorkflowUpdate } from "../types/workflow";
import { useWorkflowStore } from "../store/workflowStore";
import { toast } from "sonner"; // or your toast lib

export const QUERY_KEYS = {
  workflows: ["workflows"] as const,
  workflow: (id: string) => ["workflows", id] as const,
};

export function useWorkflowList() {
  return useQuery({ queryKey: QUERY_KEYS.workflows, queryFn: workflowsApi.list });
}

export function useWorkflow(id: string | null) {
  return useQuery({
    queryKey: QUERY_KEYS.workflow(id!),
    queryFn: () => workflowsApi.get(id!),
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: WorkflowCreate) => workflowsApi.create(data),
    onSuccess: (wf) => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.workflows });
      useWorkflowStore.getState().loadWorkflow(wf._id, wf.name, wf.nodes, wf.edges);
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
    },
  });
}
```

---

## Main Editor Page — `src/pages/WorkflowEditor.tsx`

```tsx
import ReactFlow, { Background, Controls, MiniMap, BackgroundVariant } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useWorkflowStore } from "../store/workflowStore";
import { StartNode } from "../components/nodes/StartNode";
import { ApiNode } from "../components/nodes/ApiNode";
import { ConditionNode } from "../components/nodes/ConditionNode";
import { CustomEdge } from "../components/edges/CustomEdge";
import { Sidebar } from "../components/panels/Sidebar";
import { Toolbar } from "../components/panels/Toolbar";
import { NodeEditPanel } from "../components/panels/NodeEditPanel";

const nodeTypes = {
  start: StartNode,
  api: ApiNode,
  condition: ConditionNode,
  startNode: StartNode,    // handle backend naming
  apiNode: ApiNode,
  conditionNode: ConditionNode,
};

const edgeTypes = { custom: CustomEdge };

export function WorkflowEditor() {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, selectNode, selectedNodeId } = useWorkflowStore();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-50">
      {/* Left sidebar — workflow list */}
      <Sidebar />

      {/* Main area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Toolbar />
        <div className="flex flex-1 overflow-hidden">
          <ReactFlow
            nodes={nodes as any}
            edges={edges as any}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => selectNode(node.id)}
            onPaneClick={() => selectNode(null)}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            defaultEdgeOptions={{ type: "custom" }}
            fitView
          >
            <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#e5e7eb" />
            <Controls />
            <MiniMap zoomable pannable className="!bottom-4 !right-4" />
          </ReactFlow>

          {/* Right panel — node editor */}
          {selectedNodeId && <NodeEditPanel />}
        </div>
      </div>
    </div>
  );
}
```

---

## Sidebar — `src/components/panels/Sidebar.tsx`

This component must:
- Show a scrollable list of all saved workflows from `useWorkflowList()`
- Highlight the currently active workflow (`activeWorkflowId`)
- On clicking a workflow item, call `useWorkflow(id)` and load it into the store via `loadWorkflow()`
- Have a **New Workflow** button at the top that calls `store.newWorkflow()`
- Show a **delete** icon on hover for each workflow item that calls `useDeleteWorkflow()`
- Show relative `updated_at` timestamps under each name
- Show a loading skeleton while fetching
- Width: `w-64`, fixed, left side

---

## Toolbar — `src/components/panels/Toolbar.tsx`

This component must:

**Left section — Add nodes:**
- `+ Start` button → appends `{ id: uid(), type: "start", position: {x:100,y:100}, data: {label:"Start"} }` to store nodes
- `+ API Node` button → appends api node with defaults
- `+ Condition` button → appends condition node with defaults

**Center — Workflow name:**
- Inline-editable `<input>` showing `activeWorkflowName`
- On blur/enter, calls `store.setActiveWorkflowName(value)`

**Right section — Actions:**
- **AI Generate** button (sparkle icon) → opens `AIGenerateModal`
- **Save** button → if `activeWorkflowId` exists, call `useUpdateWorkflow()`; otherwise open `SaveWorkflowModal`
- Show a `•` dirty indicator next to Save when `isDirty === true`
- Show loading spinner on save button while mutation is pending

---

## Node Edit Panel — `src/components/panels/NodeEditPanel.tsx`

Right panel, `w-72`, appears when a node is selected. Must:
- Read `selectedNodeId` from store, find the node in `nodes`
- Use **React Hook Form + Zod** for validation
- Show different fields depending on node type:
  - **All nodes:** Label (text input)
  - **API node:** Method (Select: GET/POST/PUT/DELETE), URL (text input), Headers (textarea, JSON), Body (textarea, JSON)
  - **Condition node:** Condition expression (text input, e.g. `status == 200`)
- On form submit, call `store.updateNodeData(id, data)`
- Show a **Delete Node** button at the bottom that removes the node from the store and calls `selectNode(null)`
- Auto-save on field blur (no explicit submit needed — call `updateNodeData` in `onChange`)

---

## AI Generate Modal — `src/components/modals/AIGenerateModal.tsx`

- shadcn `Dialog` component
- Large `Textarea` for the prompt
- Example placeholder: `"Fetch user data from https://api.example.com/users, if status is 200 send to Slack webhook, otherwise log the error"`
- **Generate** button calls `useGenerateWorkflow(prompt)`
- Show loading state with spinner during the API call
- On success: close modal, nodes/edges already updated in store via the mutation's `onSuccess`
- On error: show error message inside the modal — do NOT close it

---

## Save Workflow Modal — `src/components/modals/SaveWorkflowModal.tsx`

- shadcn `Dialog` with two fields: **Name** (required) and **Description** (optional)
- On submit, call `useCreateWorkflow({ name, description, nodes, edges })`
- Closes on success

---

## Wiring it all together — `src/main.tsx`

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WorkflowEditor } from "./pages/WorkflowEditor";
import "./index.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <WorkflowEditor />
    </QueryClientProvider>
  </React.StrictMode>
);
```

---

## Key Implementation Notes for Cursor

1. **Node ID generation** — use a simple counter or `crypto.randomUUID()` when adding nodes manually via the toolbar buttons.

2. **Type normalization** — when loading a workflow from the API, map `startNode → start`, `apiNode → api`, `conditionNode → condition` before putting them into the store, since ReactFlow nodeTypes uses the short names.

3. **Edge sourceHandle** — when rendering edges, pass `sourceHandleId` to `CustomEdge` so it can pick the right color (blue = normal, green = true, red = false).

4. **ReactFlow node/edge types** — register both short and long names in `nodeTypes` so workflows saved with either convention render correctly.

5. **Saving** — always send the full `nodes` and `edges` arrays on PUT (backend `WorkflowUpdate` requires them). Pull them from the store right at save time.

6. **Dirty state** — mark the store as dirty whenever nodes or edges change. Clear it after a successful save.

7. **Fit view** — call `fitView()` after loading a workflow from the API so all nodes are visible.

8. **Default edge type** — set `defaultEdgeOptions={{ type: "custom" }}` on ReactFlow so all new connections use `CustomEdge`.

9. **Connection validation** — use ReactFlow's `isValidConnection` prop to prevent connecting a node's output to its own input.

10. **Error handling** — wrap all mutation `onError` handlers with a toast notification showing the error message.
