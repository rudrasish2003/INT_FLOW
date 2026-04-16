import { useState } from "react";
import { Plus, Sparkles, Save } from "lucide-react";
import { useWorkflowStore } from "../../store/workflowStore";
import { useCreateWorkflow, useUpdateWorkflow } from "../../hooks/useWorkflows";
import { AIGenerateModal } from "../modals/AIGenerateModal";
import { SaveWorkflowModal } from "../modals/SaveWorkflowModal";

function createNode(type: "start" | "api" | "condition") {
  return {
    id: crypto.randomUUID(),
    type,
    position: { x: 100, y: 100 },
    data: {
      label: type === "start" ? "Start" : type === "api" ? "API Request" : "Condition",
      ...(type === "api" ? { method: "GET", url: "", headers: {}, body: {} } : {}),
      ...(type === "condition" ? { condition: "status == 200" } : {}),
    },
  };
}

export function Toolbar() {
  const [nameInput, setNameInput] = useState("");
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showAIModal, setShowAIModal] = useState(false);
  const { nodes, edges, activeWorkflowId, activeWorkflowName, isDirty, setActiveWorkflowName, markDirty } = useWorkflowStore();
  const setNodes = useWorkflowStore((state) => state.setNodes);
  const setEdges = useWorkflowStore((state) => state.setEdges);
  const createMutation = useCreateWorkflow();
  const updateMutation = useUpdateWorkflow();

  const handleAddNode = (type: "start" | "api" | "condition") => {
    setNodes([...nodes, createNode(type)]);
    markDirty();
  };

  const onSaveClick = () => {
    if (activeWorkflowId) {
      updateMutation.mutate({ id: activeWorkflowId, data: { name: activeWorkflowName, nodes, edges } });
    } else {
      setShowSaveModal(true);
    }
  };

  const onNameBlur = () => {
    setActiveWorkflowName(nameInput.trim() || "Untitled Workflow");
  };

  return (
    <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => handleAddNode("start")}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        >
          <Plus size={14} />
          Start
        </button>
        <button
          type="button"
          onClick={() => handleAddNode("api")}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        >
          <Plus size={14} />
          API Node
        </button>
        <button
          type="button"
          onClick={() => handleAddNode("condition")}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        >
          <Plus size={14} />
          Condition
        </button>
      </div>

      <div className="flex-1 px-4">
        <input
          value={nameInput || activeWorkflowName}
          onChange={(event) => setNameInput(event.target.value)}
          onBlur={onNameBlur}
          onKeyDown={(event) => event.key === "Enter" && onNameBlur()}
          className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-900 outline-none transition focus:border-slate-400"
          placeholder="Workflow name"
        />
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setShowAIModal(true)}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
        >
          <Sparkles size={16} />
          AI Generate
        </button>
        <button
          type="button"
          onClick={onSaveClick}
          disabled={createMutation.isLoading || updateMutation.isLoading}
          className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Save size={16} />
          Save{isDirty ? " •" : ""}
        </button>
      </div>

      <AIGenerateModal open={showAIModal} onClose={() => setShowAIModal(false)} />
      <SaveWorkflowModal
        open={showSaveModal}
        onClose={() => setShowSaveModal(false)}
        initialName={activeWorkflowName}
      />
    </div>
  );
}
