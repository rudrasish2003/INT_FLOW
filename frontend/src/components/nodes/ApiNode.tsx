import { Handle, NodeProps, Position } from "@xyflow/react";
import { useWorkflowStore } from "../../store/workflowStore";

export function ApiNode({ id, data }: NodeProps) {
  const selectNode = useWorkflowStore((s) => s.selectNode);
  const displayUrl = typeof data.url === "string" ? data.url : "";

  return (
    <div
      onClick={() => selectNode(id)}
      className="w-52 rounded-xl border-2 border-blue-500 bg-blue-50 cursor-pointer hover:border-blue-600 transition-colors"
    >
      <div className="px-3 py-2">
        <span className="text-[10px] font-bold text-blue-700 bg-blue-200 px-2 py-0.5 rounded">API</span>
        <p className="mt-1 text-sm font-medium text-blue-900 truncate">{data.label as string}</p>
        <p className="mt-1 text-[10px] text-blue-600 truncate">
          {data.method ?? "GET"} {displayUrl}
        </p>
      </div>
      <Handle type="target" position={Position.Left} className="!w-3 !h-3 !bg-blue-500" />
      <Handle type="source" position={Position.Right} id="out" className="!w-3 !h-3 !bg-blue-500" />
    </div>
  );
}
