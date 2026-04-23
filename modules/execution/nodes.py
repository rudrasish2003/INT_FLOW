import asyncio
import httpx
import json
from typing import Any, Optional
from openai import AsyncOpenAI
from core.config import settings

_openai = AsyncOpenAI(api_key=settings.openai_api_key)


async def run_node(node: dict, payload: Any) -> tuple[Any, Optional[str]]:
    node_type = node["type"]
    data = node.get("data", {})

    # ── START ────────────────────────────────────────────────────────────────
    if node_type in ("startNode", "start"):
        return payload, "out"

    # ── LLM / AI REASONING NODE ──────────────────────────────────────────────
    elif node_type == "llmNode":
        model       = data.get("llmModel", "gpt-4o")
        system_prompt = data.get("systemPrompt", "You are a helpful assistant.")
        user_prompt   = data.get("userPrompt", "")
        output_mode   = data.get("outputMode", "text")   # "text" | "json" | "decision"
        output_schema = data.get("outputSchema", "")      # JSON schema string for structured mode
        temperature   = float(data.get("temperature", 0.3))
        max_tokens    = int(data.get("maxTokens", 500))

        # Inject upstream payload into user prompt
        payload_str = json.dumps(payload, indent=2) if isinstance(payload, dict) else str(payload)
        full_user = (
            f"{user_prompt}\n\n"
            f"[Upstream data from previous node]\n{payload_str}"
        ).strip()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": full_user},
        ]

        try:
            if output_mode == "json" or output_mode == "decision":
                # Force JSON output
                schema_hint = ""
                if output_schema:
                    schema_hint = f"\n\nRespond ONLY with a JSON object matching this schema:\n{output_schema}"
                elif output_mode == "decision":
                    schema_hint = (
                        '\n\nRespond ONLY with JSON: {"decision": "yes"|"no", "reason": "string"}'
                    )
                messages[0]["content"] += schema_hint

                resp = await _openai.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                raw = resp.choices[0].message.content
                parsed = json.loads(raw)

                # Merge with upstream payload so downstream nodes see everything
                result = {**payload, "__llm_output": parsed} if isinstance(payload, dict) else {"__llm_output": parsed, "upstream": payload}

                if output_mode == "decision":
                    # Branch: "yes" → "true" handle, "no" → "false"
                    decision = str(parsed.get("decision", "no")).lower().strip()
                    result["__llm_decision"] = decision
                    handle = "true" if decision == "yes" else "false"
                    return result, handle

                return result, "out"

            else:
                # Plain text output
                resp = await _openai.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                text = resp.choices[0].message.content or ""
                result = {**payload, "__llm_output": text} if isinstance(payload, dict) else {"__llm_output": text, "upstream": payload}
                return result, "out"

        except Exception as e:
            error_out = {"__llm_error": str(e), "original_payload": payload}
            return error_out, "out"

    # ── API / WEBHOOK ────────────────────────────────────────────────────────
    elif node_type in ("apiNode", "webhookNode", "api"):
        url = data.get("url")
        method = (data.get("method") or "GET").upper()
        headers = data.get("headers") or {}

        if not url:
            return {"error": "No URL configured", "original_payload": payload}, "out"

        explicit_body = data.get("body")
        request_body = explicit_body if explicit_body else payload

        async with httpx.AsyncClient(timeout=15) as client:
            if method == "GET":
                params = (
                    {k: v for k, v in request_body.items() if isinstance(v, (str, int, float, bool))}
                    if isinstance(request_body, dict)
                    else {}
                )
                resp = await client.get(url, headers=headers, params=params)
            else:
                resp = await client.request(method, url, headers=headers, json=request_body)

        try:
            result = resp.json()
        except Exception:
            result = {"raw": resp.text, "status_code": resp.status_code}

        if isinstance(result, dict):
            result.setdefault("status_code", resp.status_code)

        return result, "out"

    # ── CONDITION ────────────────────────────────────────────────────────────
    elif node_type in ("conditionNode", "condition"):
        variable = data.get("conditionVariable", "")
        operator = data.get("conditionOperator", "==")
        value    = data.get("conditionValue", "")

        try:
            lhs = payload
            if variable and isinstance(payload, dict):
                for key in variable.split("."):
                    lhs = lhs[key] if isinstance(lhs, dict) else lhs

            ops = {
                "==":         lambda a, b: str(a) == str(b),
                "!=":         lambda a, b: str(a) != str(b),
                ">":          lambda a, b: float(a) > float(b),
                "<":          lambda a, b: float(a) < float(b),
                ">=":         lambda a, b: float(a) >= float(b),
                "<=":         lambda a, b: float(a) <= float(b),
                "exists":     lambda a, b: a is not None,
                "not_exists": lambda a, b: a is None,
            }

            result = ops.get(operator, lambda a, b: False)(lhs, value)
            handle = "true" if result else "false"
        except Exception as exc:
            payload = {**payload, "__condition_error": str(exc)} if isinstance(payload, dict) else payload
            handle = "false"

        return payload, handle

    # ── FUNCTION (inline Python) ──────────────────────────────────────────────
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

    # ── DELAY ─────────────────────────────────────────────────────────────────
    elif node_type == "delayNode":
        timeout = float(data.get("timeout", 1))
        await asyncio.sleep(timeout)
        return payload, "out"

    # ── TERMINAL NODES ────────────────────────────────────────────────────────
    elif node_type in ("endNode", "debugNode", "end"):
        return payload, None

    # ── UNKNOWN — pass through ────────────────────────────────────────────────
    return payload, "out"