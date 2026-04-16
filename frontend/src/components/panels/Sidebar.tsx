import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { useWorkflowStore } from "../../store/workflowStore";
import { useDeleteWorkflow, useWorkflow, useWorkflowList } from "../../hooks/useWorkflows";

function relativeTime(updatedAt: string) {
  const date = new Date(updatedAt);
  const delta = Math.round((date.getTime() - Date.now()) / 1000);
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

  if (Math.abs(delta) < 60) return rtf.format(delta, "second");
  const minutes = Math.round(delta / 60);
  if (Math.abs(minutes) < 60) return rtf.format(minutes, "minute");
  const hours = Math.round(minutes / 60);
  if (Math.abs(hours) < 24) return rtf.format(hours, "hour");
  const days = Math.round(hours / 24);
  return rtf.format(days, "day");
}

export function Sidebar() {
  const newWorkflow = useWorkflowStore((state) => state.newWorkflow);
  const loadWorkflow = useWorkflowStore((state) => state.loadWorkflow);
  const activeWorkflowId = useWorkflowStore((state) => state.activeWorkflowId);
  const { data: workflows, isLoading } = useWorkflowList();
  const { mutate: deleteWorkflow } = useDeleteWorkflow();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const workflowQuery = useWorkflow(selectedId);

  useEffect(() => {
    if (workflowQuery.data) {
      const normalizedNodes = workflowQuery.data.nodes.map((node) => ({
        ...node,
        type:
          node.type === "startNode"
            ? "start"
            : node.type === "apiNode"
            ? "api"
            : node.type === "conditionNode"
            ? "condition"
            : node.type,
      }));
      loadWorkflow(workflowQuery.data._id, workflowQuery.data.name, normalizedNodes, workflowQuery.data.edges);
    }
  }, [workflowQuery.data, loadWorkflow]);

  return (
    <aside className="w-64 border-r border-slate-200 bg-white p-4 flex flex-col gap-4">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Workflows</h2>
          <p className="text-xs text-slate-500">Saved workflows</p>
        </div>
        <button
          type="button"
          onClick={() => {
            newWorkflow();
            setSelectedId(null);
          }}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-white transition hover:bg-slate-700"
          aria-label="New workflow"
        >
          <Plus size={16} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="h-16 animate-pulse rounded-xl bg-slate-100" />
          ))
        ) : (
          workflows?.map((workflow) => (
            <div
              key={workflow.id}
              className={`group relative rounded-2xl border p-3 transition ${workflow.id === activeWorkflowId ? "border-slate-900 bg-slate-100" : "border-slate-200 bg-white hover:border-slate-300"}`}
            >
              <button
                type="button"
                className="text-left w-full"
                onClick={() => setSelectedId(workflow.id)}
              >
                <div className="text-sm font-semibold text-slate-900">{workflow.name}</div>
                <div className="mt-1 text-xs text-slate-500">Updated {relativeTime(workflow.updated_at)}</div>
              </button>
              <button
                type="button"
                onClick={() => deleteWorkflow(workflow.id)}
                className="absolute right-3 top-3 hidden rounded-full p-1 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 group-hover:inline-flex"
                aria-label="Delete workflow"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
