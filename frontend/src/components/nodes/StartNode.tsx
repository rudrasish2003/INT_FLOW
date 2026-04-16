import { Handle, NodeProps, Position } from "@xyflow/react";
import { useWorkflowStore } from "../../store/workflowStore";

export function StartNode({ id, data }: NodeProps) {
  const selectNode = useWorkflowStore((s) => s.selectNode);

  return (
    <div
      onClick={() => selectNode(id)}
      className="w-44 rounded-xl border-2 border-emerald-500 bg-emerald-50 cursor-pointer hover:border-emerald-600 transition-colors"
    >
      <div className="px-3 py-2">
        <span className="text-[10px] font-bold text-emerald-700 bg-emerald-200 px-2 py-0.5 rounded">
          START
        </span>
        <p className="mt-1 text-sm font-medium text-emerald-900 truncate">{data.label as string}</p>
      </div>
      <Handle type="source" position={Position.Right} id="out" className="!w-3 !h-3 !bg-emerald-500" />
    </div>
  );
}
