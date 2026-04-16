import { useState, useEffect } from "react";
import { X } from "lucide-react";
import { useGenerateWorkflow } from "../../hooks/useWorkflows";

interface AIGenerateModalProps {
  open: boolean;
  onClose: () => void;
}

export function AIGenerateModal({ open, onClose }: AIGenerateModalProps) {
  const [prompt, setPrompt] = useState("");
  const mutation = useGenerateWorkflow();

  useEffect(() => {
    if (!open) {
      setPrompt("");
    }
  }, [open]);

  useEffect(() => {
    if (mutation.isSuccess) {
      onClose();
    }
  }, [mutation.isSuccess, onClose]);

  if (!open) return null;

  return (
    <div className="modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Generate Workflow with AI</h2>
            <p className="mt-1 text-sm text-slate-500">Enter a prompt and let the backend generate nodes and edges.</p>
          </div>
          <button type="button" onClick={onClose} className="rounded-full p-2 text-slate-500 hover:bg-slate-100">
            <X size={18} />
          </button>
        </div>

        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="Fetch user data from https://api.example.com/users, if status is 200 send to Slack webhook, otherwise log the error"
          className="mt-4 min-h-[160px] w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-400"
        />

        {mutation.isError && (
          <div className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
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
            onClick={() => mutation.mutate(prompt)}
            disabled={mutation.isLoading || prompt.trim().length === 0}
            className="inline-flex items-center justify-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {mutation.isLoading ? "Generating..." : "Generate"}
          </button>
        </div>
      </div>
    </div>
  );
}
