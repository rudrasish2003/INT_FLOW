import { BaseEdge, EdgeLabelRenderer, getBezierPath, EdgeProps } from "@xyflow/react";

export function CustomEdge({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, label, sourceHandleId }: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
  const color = sourceHandleId === "true" ? "#1D9E75" : sourceHandleId === "false" ? "#E24B4A" : "#378ADD";

  return (
    <>
      <BaseEdge path={edgePath} style={{ stroke: color, strokeWidth: 2 }} />
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{ transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)` }}
            className="absolute text-[10px] bg-white border border-slate-200 px-1.5 py-0.5 rounded pointer-events-none"
          >
            {label as string}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
