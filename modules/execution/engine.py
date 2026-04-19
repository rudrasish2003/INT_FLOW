import asyncio
from typing import Any
from datetime import datetime, timezone
from .nodes import run_node


class WorkflowEngine:
    def __init__(self, workflow_id: str, nodes: list, edges: list):
        self.workflow_id = workflow_id
        self.nodes = {n["id"]: n for n in nodes}
        self.edges = edges
        self.status = "idle"
        self.logs: list[dict] = []
        self._task: asyncio.Task | None = None

    def _find_start_id(self) -> str | None:
        for node_id, node in self.nodes.items():
            if node["type"] in ("startNode", "start"):
                return node_id
        return None

    def _get_next_nodes(self, source_id: str, handle: str) -> list[str]:
        results = []
        for edge in self.edges:
            if edge["source"] != source_id:
                continue
            edge_handle = edge.get("sourceHandle") or "out"
            if edge_handle == handle:
                results.append(edge["target"])
        return results

    def _log(self, node_id: str, label: str, payload: Any, status: str = "ok"):
        self.logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node_id": node_id,
            "label": label,
            "payload": payload,
            "status": status,
        })

    async def _run(self, initial_payload: Any):
        self.status = "running"
        self.logs = []

        start_id = self._find_start_id()
        if not start_id:
            self.status = "error"
            self._log("—", "No startNode found", None, "error")
            return

        queue: list[tuple[str, Any]] = [(start_id, initial_payload)]
        visited: set[str] = set()

        while queue:
            node_id, payload = queue.pop(0)

            if node_id in visited:
                continue
            visited.add(node_id)

            node = self.nodes.get(node_id)
            if not node:
                continue

            label = node.get("data", {}).get("label", node_id)
            try:
                output, handle = await run_node(node, payload)
                self._log(node_id, label, output, "ok")

                if handle is None:
                    continue  # Terminal node, stop this branch

                next_ids = self._get_next_nodes(node_id, handle)
                for next_id in next_ids:
                    queue.append((next_id, output))

            except Exception as e:
                self._log(node_id, label, str(e), "error")
                self.status = "error"
                return

        self.status = "completed"

    def start(self, initial_payload: Any = None):
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._run(initial_payload or {}))

    def stop(self):
        if self._task and not self._task.done():
            self._task.cancel()
        self.status = "stopped"

    def get_state(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "logs": self.logs,
        }