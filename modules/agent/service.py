import json
import httpx
from openai import AsyncOpenAI
from core.config import settings
from .schemas import ChatRequest, ChatResponse

client = AsyncOpenAI(api_key=settings.openai_api_key)

BASE = "http://localhost:8000"

# ── Workflow registry ─────────────────────────────────────────────────────────
# Each workflow is a list of steps. Each step has:
#   url, method, and optional condition to pick the next step.
WORKFLOWS = {
    "wfh": {
        "name": "Work From Home",
        "keywords": ["wfh", "work from home", "work at home", "remote"],
        "fields": ["emp_id", "date"],
        "steps": [
            {"label": "Check WFH eligibility", "url": f"{BASE}/api/demo/wfh/check",  "method": "POST"},
            {
                "label": "Branch on eligibility",
                "condition": True,   # inspect is_eligible from previous output
                "true":  {"label": "Approve WFH", "url": f"{BASE}/api/demo/wfh/apply",  "method": "POST"},
                "false": {"label": "Reject WFH",  "url": f"{BASE}/api/demo/wfh/reject", "method": "POST"},
            },
        ],
    },
    "leave": {
        "name": "Leave Application",
        "keywords": ["leave", "day off", "vacation", "holiday", "sick"],
        "fields": ["emp_id", "from_date", "to_date", "reason"],
        "steps": [
            {"label": "Check leave eligibility", "url": f"{BASE}/api/demo/wfh/leave/check",  "method": "POST"},
            {
                "label": "Branch on eligibility",
                "condition": True,
                "true":  {"label": "Approve leave", "url": f"{BASE}/api/demo/wfh/leave/apply",  "method": "POST"},
                "false": {"label": "Reject leave",  "url": f"{BASE}/api/demo/wfh/leave/reject", "method": "POST"},
            },
        ],
    },
}

# ── Prompt ────────────────────────────────────────────────────────────────────
SYSTEM = """You are an HR assistant that handles Work From Home (WFH) and Leave requests.

Available workflows:
1. WFH - requires: emp_id (e.g. EMP001), date (YYYY-MM-DD)
2. Leave - requires: emp_id, from_date (YYYY-MM-DD), to_date (YYYY-MM-DD), reason

Rules:
- Detect the intent from user message (wfh / leave / unknown).
- Extract any values the user already provided.
- If intent is unknown, ask what they need.
- If values are missing, ask for ONE missing value at a time in a friendly way.
- Once you have all values, confirm you're about to execute.
- Always respond in JSON only — no prose outside the JSON.

Respond ONLY with this JSON (no markdown fences):
{
  "intent": "wfh" | "leave" | "unknown",
  "reply": "your friendly message to the user",
  "extracted": { "key": "value" },
  "ready": true | false
}"""

# ── In-memory sessions ────────────────────────────────────────────────────────
_sessions: dict[str, dict] = {}


def _session(sid: str) -> dict:
    if sid not in _sessions:
        _sessions[sid] = {
            "intent": None,
            "collected": {},
            "history": [],    # [{role, content}]
            "done": False,
        }
    return _sessions[sid]


# ── Workflow executor ─────────────────────────────────────────────────────────
async def _execute(intent: str, payload: dict) -> dict:
    """
    Run the workflow steps. Returns dict with keys:
      steps: list of {label, payload}
      final: last payload
      missing: list of missing field names (if any step returned 422)
    """
    wf = WORKFLOWS[intent]
    steps_log = []
    current = dict(payload)

    for step in wf["steps"]:
        if step.get("condition"):
            # Branch based on is_eligible from previous payload
            eligible = str(current.get("is_eligible", "no")).lower() == "yes"
            next_step = step["true"] if eligible else step["false"]
            async with httpx.AsyncClient(timeout=15) as h:
                r = await h.request(next_step["method"], next_step["url"], json=current)
            body = r.json()
            if r.status_code == 422 and body.get("error") == "missing_fields":
                return {"steps": steps_log, "final": current, "missing": body["missing"]}
            steps_log.append({"label": next_step["label"], "payload": body, "status": r.status_code})
            current = body
        else:
            async with httpx.AsyncClient(timeout=15) as h:
                r = await h.request(step["method"], step["url"], json=current)
            body = r.json()
            if r.status_code == 422 and body.get("error") == "missing_fields":
                return {"steps": steps_log, "final": current, "missing": body["missing"]}
            steps_log.append({"label": step["label"], "payload": body, "status": r.status_code})
            current = body

    return {"steps": steps_log, "final": current, "missing": []}


# ── Main chat handler ─────────────────────────────────────────────────────────
async def handle_chat(req: ChatRequest) -> ChatResponse:
    sess = _session(req.session_id)

    if sess["done"]:
        # Reset for a new conversation
        _sessions[req.session_id] = {
            "intent": None, "collected": {}, "history": [], "done": False
        }
        sess = _sessions[req.session_id]

    # Build messages for AI
    sess["history"].append({"role": "user", "content": req.message})

    # Add session context into system prompt so AI knows what's collected
    ctx = ""
    if sess["intent"] or sess["collected"]:
        ctx = (
            f"\n\n[SESSION STATE]\nintent={sess['intent']}\n"
            f"already_collected={json.dumps(sess['collected'])}"
        )

    messages = [{"role": "system", "content": SYSTEM + ctx}] + sess["history"]

    # Call GPT
    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.3,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content
    ai = json.loads(raw)

    reply     = ai.get("reply", "How can I help you?")
    intent    = ai.get("intent") or sess["intent"]
    extracted = ai.get("extracted") or {}
    ready     = ai.get("ready", False)

    # Persist to session
    if intent and intent != "unknown":
        sess["intent"] = intent
    sess["collected"].update({k: v for k, v in extracted.items() if v})
    sess["history"].append({"role": "assistant", "content": reply})

    # If not ready yet, just return the AI reply
    if not ready or not sess["intent"] or sess["intent"] == "unknown":
        return ChatResponse(
            reply=reply,
            status="collecting",
            collected=sess["collected"] or None,
        )

    # ── Ready to execute ──────────────────────────────────────────────────────
    result = await _execute(sess["intent"], sess["collected"])

    if result["missing"]:
        # Workflow told us fields are still missing — ask AI to request them
        missing_str = ", ".join(result["missing"])
        follow_up_msgs = messages + [
            {"role": "assistant", "content": reply},
            {
                "role": "user",
                "content": (
                    f"The workflow API returned an error saying these fields are missing: {missing_str}. "
                    f"Please ask the user for them one by one. Set ready=false."
                ),
            },
        ]
        r2 = await client.chat.completions.create(
            model="gpt-4o",
            messages=follow_up_msgs,
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        ai2   = json.loads(r2.choices[0].message.content)
        reply2 = ai2.get("reply", f"I still need: {missing_str}. Can you provide them?")
        sess["history"].append({"role": "assistant", "content": reply2})
        return ChatResponse(
            reply=reply2,
            status="collecting",
            collected=sess["collected"] or None,
        )

    # ── Workflow completed ────────────────────────────────────────────────────
    final   = result["final"]
    summary = (
        final.get("final_message")
        or final.get("message")
        or f"Done! Status: {final.get('status', 'completed')}"
    )
    full_reply = f"{reply}\n\n✅ {summary}"
    sess["done"] = True

    return ChatResponse(
        reply=full_reply,
        status="done",
        workflow_result=result,
        collected=sess["collected"],
    )


def reset_session(session_id: str):
    _sessions.pop(session_id, None)