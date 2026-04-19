import asyncio
import httpx
from typing import Any, Optional

async def run_node(node: dict, payload: Any) -> tuple[Any, Optional[str]]:
    node_type = node["type"]
    data = node.get("data", {})

    if node_type in ("startNode", "start"):
        return payload, "out"

    elif node_type in ("apiNode", "webhookNode", "api"):
        url = data.get("url")
        method = (data.get("method") or "GET").upper()
        headers = data.get("headers") or {}
        body = data.get("body") or payload
        if not url:
            return {"error": "No URL configured"}, "out"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.request(
                method, url,
                headers=headers,
                json=body if method != "GET" else None
            )
            try:
                return resp.json(), "out"
            except Exception:
                return {"raw": resp.text}, "out"

    elif node_type in ("conditionNode", "condition"):
        variable = data.get("conditionVariable", "payload")
        operator = data.get("conditionOperator", "==")
        value = data.get("conditionValue", "")
        condition_str = data.get("condition", "")

        try:
            if condition_str:
                result = eval(condition_str, {"payload": payload})
            else:
                # Use structured fields
                lhs = payload.get(variable, payload) if isinstance(payload, dict) else payload
                ops = {
                    "==": lambda a, b: a == b,
                    "!=": lambda a, b: a != b,
                    ">":  lambda a, b: float(a) > float(b),
                    "<":  lambda a, b: float(a) < float(b),
                    ">=": lambda a, b: float(a) >= float(b),
                    "<=": lambda a, b: float(a) <= float(b),
                }
                result = ops.get(operator, lambda a, b: False)(lhs, value)
            handle = "true" if result else "false"
        except Exception:
            handle = "false"
        return payload, handle

    elif node_type == "functionNode":
        code = data.get("code", "")
        local_vars = {"payload": payload}
        try:
            indented = "\n".join(f"    {line}" for line in code.splitlines())
            exec(f"def _fn(payload):\n{indented}\n    return payload", local_vars)
            output = local_vars["_fn"](payload)
        except Exception as e:
            output = {"error": str(e), "original_payload": payload}
        return output, "out"

    elif node_type == "delayNode":
        timeout = float(data.get("timeout", 1))
        await asyncio.sleep(timeout)
        return payload, "out"

    elif node_type in ("endNode", "debugNode"):
        return payload, None  # Terminal

    # Unknown node type — pass through
    return payload, "out"