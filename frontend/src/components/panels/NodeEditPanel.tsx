import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useWorkflowStore } from "../../store/workflowStore";

const nodeFormSchema = z.object({
  label: z.string().min(1, "Label is required"),
  method: z.enum(["GET", "POST", "PUT", "DELETE"]).optional(),
  url: z.string().optional(),
  headers: z.string().optional(),
  body: z.string().optional(),
  condition: z.string().optional(),
});

type NodeFormValues = z.infer<typeof nodeFormSchema>;

function safeJson(value?: string) {
  if (!value) return {};
  try {
    return JSON.parse(value);
  } catch {
    return undefined;
  }
}

export function NodeEditPanel() {
  const { selectedNodeId, nodes, updateNodeData, selectNode } = useWorkflowStore();
  const node = nodes.find((item) => item.id === selectedNodeId);

  const { register, handleSubmit, reset, formState } = useForm<NodeFormValues>({
    resolver: zodResolver(nodeFormSchema),
    defaultValues: {
      label: node?.data.label ?? "",
      method: node?.data.method,
      url: node?.data.url,
      headers: node?.data.headers ? JSON.stringify(node.data.headers, null, 2) : "",
      body: node?.data.body ? JSON.stringify(node.data.body, null, 2) : "",
      condition: node?.data.condition,
    },
    mode: "onBlur",
  });

  useEffect(() => {
    if (node) {
      reset({
        label: node.data.label,
        method: node.data.method,
        url: node.data.url,
        headers: node.data.headers ? JSON.stringify(node.data.headers, null, 2) : "",
        body: node.data.body ? JSON.stringify(node.data.body, null, 2) : "",
        condition: node.data.condition,
      });
    }
  }, [node, reset]);

  const saveNode = (values: NodeFormValues) => {
    const headers = safeJson(values.headers);
    const body = safeJson(values.body);

    if (values.headers && headers === undefined) return;
    if (values.body && body === undefined) return;

    updateNodeData(node!.id, {
      label: values.label,
      method: values.method,
      url: values.url,
      headers: headers ?? undefined,
      body: body ?? undefined,
      condition: values.condition,
    });
  };

  if (!node) return null;

  return (
    <aside className="w-72 border-l border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-900">Node settings</h2>
        <button
          type="button"
          onClick={() => {
            useWorkflowStore.getState().setNodes(nodes.filter((item) => item.id !== node.id));
            useWorkflowStore.getState().setEdges(useWorkflowStore.getState().edges.filter((edge) => edge.source !== node.id && edge.target !== node.id));
            selectNode(null);
          }}
          className="text-xs text-rose-600 hover:text-rose-800"
        >
          Delete Node
        </button>
      </div>

      <form className="mt-4 space-y-4" onBlur={handleSubmit(saveNode)}>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Label</label>
          <input
            {...register("label")}
            className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-400"
          />
          {formState.errors.label && (
            <p className="mt-1 text-xs text-rose-600">{formState.errors.label.message}</p>
          )}
        </div>

        {node.type === "api" || node.type === "apiNode" ? (
          <>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Method</label>
              <select
                {...register("method")}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-400"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">URL</label>
              <input
                {...register("url")}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-400"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Headers (JSON)</label>
              <textarea
                {...register("headers")}
                rows={4}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-400"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Body (JSON)</label>
              <textarea
                {...register("body")}
                rows={4}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-400"
              />
            </div>
          </>
        ) : null}

        {node.type === "condition" || node.type === "conditionNode" ? (
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Condition</label>
            <input
              {...register("condition")}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-400"
            />
          </div>
        ) : null}
      </form>
    </aside>
  );
}
