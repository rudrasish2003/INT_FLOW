import { Handle, NodeProps, Position } from "@xyflow/react";
import { useWorkflowStore } from "../../store/workflowStore";

export function ConditionNode({ id, data }: NodeProps) {
  const selectNode = useWorkflowStore((s) => s.selectNode);

  return (
    <div
      onClick={() => selectNode(id)}
      className="w-52 rounded-xl border-2 border-amber-500 bg-amber-50 cursor-pointer hover:border-amber-600 transition-colors"
    >
      <div className="px-3 py-2">
        <span className="text-[10px] font-bold text-amber-700 bg-amber-200 px-2 py-0.5 rounded">
          CONDITION
        </span>
        <p className="mt-1 text-sm font-medium text-amber-900 truncate">{data.label as string}</p>
        <p className="mt-1 text-[10px] text-amber-600 truncate">{data.condition as string}</p>
      </div>
      <Handle type="target" position={Position.Left} className="!w-3 !h-3 !bg-amber-500" />
      <div className="relative">
        <Handle type="source" position={Position.Bottom} id="true" className="!w-3 !h-3 !bg-emerald-500" />
        <span className="absolute left-1/2 top-4 -translate-x-1/2 text-[10px] text-emerald-700">true</span>
      </div>
      <div className="relative mt-2">
        <Handle type="source" position={Position.Right} id="false" className="!w-3 !h-3 !bg-rose-500" />
        <span className="absolute right-0 top-1 text-[10px] text-rose-700">false</span>
      </div>
    </div>
  );
}
