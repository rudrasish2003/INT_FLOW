import { useState, useEffect } from "react";
import { X } from "lucide-react";
import { useCreateWorkflow } from "../../hooks/useWorkflows";
import { useWorkflowStore } from "../../store/workflowStore";

interface SaveWorkflowModalProps {
  open: boolean;
  onClose: () => void;
  initialName: string;
}

export function SaveWorkflowModal({ open, onClose, initialName }: SaveWorkflowModalProps) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState("");
  const { nodes, edges } = useWorkflowStore();
  const mutation = useCreateWorkflow();

  useEffect(() => {
    if (!open) {
      setName(initialName);
      setDescription("");
    }
  }, [open, initialName]);

  useEffect(() => {
    if (mutation.isSuccess) {
      onClose();
    }
  }, [mutation.isSuccess, onClose]);

  if (!open) return null;

  const onSubmit = () => {
    if (!name.trim()) return;
    mutation.mutate({ name: name.trim(), description: description.trim() || undefined, nodes, edges });
  };

  return (
    <div className="modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Save Workflow</h2>
            <p className="mt-1 text-sm text-slate-500">Enter a name and optional description for this workflow.</p>
          </div>
          <button type="button" onClick={onClose} className="rounded-full p-2 text-slate-500 hover:bg-slate-100">
            <X size={18} />
          </button>
        </div>

        <div className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Name</label>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-2 w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-400"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Description</label>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={4}
              className="mt-2 w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-400"
            />
          </div>
        </div>

        {mutation.isError && (
          <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {String(mutation.error)}
          </div>
        )}

        <div className="mt-5 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onSubmit}
            disabled={mutation.isLoading || !name.trim()}
            className="inline-flex items-center justify-center rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {mutation.isLoading ? "Saving..." : "Save Workflow"}
          </button>
        </div>
      </div>
    </div>
  );
}
