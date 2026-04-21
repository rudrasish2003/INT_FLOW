import asyncio
import httpx
from typing import Any, Optional


async def run_node(node: dict, payload: Any) -> tuple[Any, Optional[str]]:
    node_type = node["type"]
    data = node.get("data", {})

    # ── START ────────────────────────────────────────────────────────────────
    if node_type in ("startNode", "start"):
        return payload, "out"

    # ── API / WEBHOOK ────────────────────────────────────────────────────────
    elif node_type in ("apiNode", "webhookNode", "api"):
        url = data.get("url")
        method = (data.get("method") or "GET").upper()
        headers = data.get("headers") or {}

        if not url:
            return {"error": "No URL configured", "original_payload": payload}, "out"

        # If the node has an explicit body configured, use it.
        # Otherwise forward the upstream payload.
        explicit_body = data.get("body")
        request_body = explicit_body if explicit_body else payload

        async with httpx.AsyncClient(timeout=15) as client:
            if method == "GET":
                # For GET requests, pass the payload as query parameters so it
                # isn't silently dropped.  Only scalar values are forwarded.
                params = (
                    {k: v for k, v in request_body.items() if isinstance(v, (str, int, float, bool))}
                    if isinstance(request_body, dict)
                    else {}
                )
                resp = await client.get(url, headers=headers, params=params)
            else:
                resp = await client.request(
                    method, url, headers=headers, json=request_body
                )

        try:
            result = resp.json()
        except Exception:
            result = {"raw": resp.text, "status_code": resp.status_code}

        # Always inject the HTTP status so downstream condition nodes can
        # branch on it without extra configuration.
        if isinstance(result, dict):
            result.setdefault("status_code", resp.status_code)

        return result, "out"

    # ── CONDITION ────────────────────────────────────────────────────────────
    elif node_type in ("conditionNode", "condition"):
        variable   = data.get("conditionVariable", "")
        operator   = data.get("conditionOperator", "==")
        value      = data.get("conditionValue", "")

        try:
            # Resolve the left-hand side from the payload dict.
            # Supports dot-notation: "user.status"
            lhs = payload
            if variable and isinstance(payload, dict):
                for key in variable.split("."):
                    lhs = lhs[key] if isinstance(lhs, dict) else lhs

            ops = {
                "==":        lambda a, b: str(a) == str(b),
                "!=":        lambda a, b: str(a) != str(b),
                ">":         lambda a, b: float(a) > float(b),
                "<":         lambda a, b: float(a) < float(b),
                ">=":        lambda a, b: float(a) >= float(b),
                "<=":        lambda a, b: float(a) <= float(b),
                "exists":    lambda a, b: a is not None,
                "not_exists":lambda a, b: a is None,
            }

            result = ops.get(operator, lambda a, b: False)(lhs, value)
            handle = "true" if result else "false"
        except Exception as exc:
            # If evaluation fails, treat as false and surface the error in
            # the payload so it's visible in the execution panel.
            payload = {**payload, "__condition_error": str(exc)} if isinstance(payload, dict) else payload
            handle = "false"

        return payload, handle

    # ── FUNCTION (inline Python) ─────────────────────────────────────────────
    elif node_type == "functionNode":
        code = data.get("code", "")
        local_vars: dict = {}
        try:
            indented = "\n".join(f"    {line}" for line in code.splitlines())
            exec(
                f"def _fn(payload):\n{indented if indented.strip() else '    pass'}\n    return payload",
                local_vars,
            )
            output = local_vars["_fn"](payload)
        except Exception as e:
            output = {"error": str(e), "original_payload": payload}
        return output, "out"

    # ── DELAY ────────────────────────────────────────────────────────────────
    elif node_type == "delayNode":
        timeout = float(data.get("timeout", 1))
        await asyncio.sleep(timeout)
        return payload, "out"

    # ── TERMINAL NODES ───────────────────────────────────────────────────────
    elif node_type in ("endNode", "debugNode", "end"):
        # Return None handle to signal the engine to stop this branch.
        return payload, None

    # ── UNKNOWN — pass through ───────────────────────────────────────────────
    return payload, "out"