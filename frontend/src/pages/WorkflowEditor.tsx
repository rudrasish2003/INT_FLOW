import React from "react";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
} from "@xyflow/react";
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
  startNode: StartNode,
  apiNode: ApiNode,
  conditionNode: ConditionNode,
};

const edgeTypes = { custom: CustomEdge };

export function WorkflowEditor() {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    selectNode,
    selectedNodeId,
  } = useWorkflowStore();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900">
      <Sidebar />
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
            isValidConnection={(connection) => connection.source !== connection.target}
          >
            <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#cbd5e1" />
            <Controls />
            <MiniMap zoomable pannable className="!bottom-4 !right-4" />
          </ReactFlow>
          {selectedNodeId && <NodeEditPanel />}
        </div>
      </div>
    </div>
  );
}
