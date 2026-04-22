import json
import httpx
from datetime import date, timedelta
from openai import AsyncOpenAI
from core.config import settings
from .schemas import ChatRequest, ChatResponse

client = AsyncOpenAI(api_key=settings.openai_api_key)

BASE = "http://localhost:8000"

WORKFLOWS = {
    "wfh": {
        "name": "Work From Home",
        "fields": ["emp_id", "date"],
        "steps": [
            {
                "label": "Check WFH eligibility",
                "url": f"{BASE}/api/demo/wfh/check",
                "method": "POST",
                # Only send these keys to this endpoint
                "send_fields": ["emp_id", "date"],
            },
            {
                "label": "Branch on eligibility",
                "condition": True,
                "true": {
                    "label": "Approve WFH",
                    "url": f"{BASE}/api/demo/wfh/apply",
                    "method": "POST",
                    "send_fields": None,  # send everything (includes is_eligible etc from prev step)
                },
                "false": {
                    "label": "Reject WFH",
                    "url": f"{BASE}/api/demo/wfh/reject",
                    "method": "POST",
                    "send_fields": None,
                },
            },
        ],
    },
    "leave": {
        "name": "Leave Application",
        "fields": ["emp_id", "from_date", "to_date", "reason"],
        "steps": [
            {
                "label": "Check leave eligibility",
                "url": f"{BASE}/api/demo/wfh/leave/check",
                "method": "POST",
                "send_fields": ["emp_id", "from_date", "to_date", "reason"],
            },
            {
                "label": "Branch on eligibility",
                "condition": True,
                "true": {
                    "label": "Approve leave",
                    "url": f"{BASE}/api/demo/wfh/leave/apply",
                    "method": "POST",
                    "send_fields": None,
                },
                "false": {
                    "label": "Reject leave",
                    "url": f"{BASE}/api/demo/wfh/leave/reject",
                    "method": "POST",
                    "send_fields": None,
                },
            },
        ],
    },
}

# ── Field name aliases ────────────────────────────────────────────────────────
FIELD_ALIASES: dict[str, str] = {
    "employee_id":     "emp_id",
    "employeeid":      "emp_id",
    "employee_number": "emp_id",
    "employee":        "emp_id",
    "emp":             "emp_id",
    "staff_id":        "emp_id",
    "id":              "emp_id",

    "wfh_date":        "date",
    "work_date":       "date",
    "requested_date":  "date",
    "day":             "date",
    "wfh_day":         "date",

    "start_date":      "from_date",
    "leave_start":     "from_date",
    "leave_from":      "from_date",
    "from":            "from_date",
    "start":           "from_date",

    "end_date":        "to_date",
    "leave_end":       "to_date",
    "leave_to":        "to_date",
    "to":              "to_date",
    "end":             "to_date",

    "leave_reason":    "reason",
    "purpose":         "reason",
    "description":     "reason",
    "cause":           "reason",
}


def _normalize(raw: dict) -> dict:
    out = {}
    for k, v in raw.items():
        key = FIELD_ALIASES.get(k.lower().strip(), k.lower().strip())
        if v is not None and str(v).strip():
            out[key] = str(v).strip()
    return out


def _resolve_date(value: str, today: date) -> str:
    if not value:
        return value
    v = value.strip().lower()
    if v == "today":
        return today.isoformat()
    if v in ("tomorrow", "tmr", "tmrw"):
        return (today + timedelta(days=1)).isoformat()
    if v in ("day after tomorrow", "day after"):
        return (today + timedelta(days=2)).isoformat()
    weekdays = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    for i, wd in enumerate(weekdays):
        if f"next {wd}" in v or v == wd:
            days = (i - today.weekday()) % 7 or 7
            return (today + timedelta(days=days)).isoformat()
        if f"this {wd}" in v:
            days = (i - today.weekday()) % 7
            return (today + timedelta(days=days)).isoformat()
    # already YYYY-MM-DD
    if len(value) == 10 and value[4] == "-" and value[7] == "-":
        return value
    return value


def _resolve_dates(payload: dict, today: date) -> dict:
    out = dict(payload)
    for f in ("date", "from_date", "to_date"):
        if f in out:
            out[f] = _resolve_date(out[f], today)
    return out


def _missing(intent: str, collected: dict) -> list[str]:
    return [f for f in WORKFLOWS[intent]["fields"] if not collected.get(f)]


def _build_payload(step: dict, current: dict) -> dict:
    """Send only the fields the endpoint needs, nothing extra."""
    fields = step.get("send_fields")
    if fields is None:
        return current
    return {k: current[k] for k in fields if k in current}


# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM = """You are Maya, a friendly HR assistant. Help employees with WFH requests and leave applications.

Be warm, natural, conversational — like a helpful colleague. Keep replies short (1-3 sentences).

STRICT RULE — always use EXACTLY these field names in "extracted":
  "emp_id"    — employee ID (e.g. "EMP001")
  "date"      — WFH date
  "from_date" — leave start date
  "to_date"   — leave end date
  "reason"    — leave reason

Dates: accept natural language ("tomorrow", "next Monday") — include them as-is.

Respond ONLY in this JSON format:
{
  "reply": "natural friendly message",
  "intent": "wfh" | "leave" | "unknown",
  "extracted": {},
  "ready": false
}

Set ready=true ONLY when you have ALL fields:
- WFH:   emp_id + date
- Leave: emp_id + from_date + to_date + reason

Never mention field names to the user. Ask for one thing at a time naturally."""


_sessions: dict[str, dict] = {}


def _get_session(sid: str) -> dict:
    if sid not in _sessions:
        _sessions[sid] = {"intent": None, "collected": {}, "history": [], "done": False}
    return _sessions[sid]


# ── Workflow executor ─────────────────────────────────────────────────────────
async def _execute(intent: str, payload: dict) -> dict:
    steps_log = []
    current = dict(payload)

    for step in WORKFLOWS[intent]["steps"]:
        if step.get("condition"):
            eligible = str(current.get("is_eligible", "no")).lower() == "yes"
            branch = step["true"] if eligible else step["false"]
            send = _build_payload(branch, current)
            print(f"[execute] {branch['label']} → POST {branch['url']}")
            print(f"[execute] payload: {send}")
            async with httpx.AsyncClient(timeout=15) as h:
                r = await h.post(branch["url"], json=send)
            print(f"[execute] response {r.status_code}: {r.text[:200]}")
            body = r.json()
            if r.status_code == 422:
                return {"steps": steps_log, "final": current, "missing": body.get("missing", [])}
            steps_log.append({"label": branch["label"], "payload": body, "status": r.status_code})
            current = {**current, **body}
        else:
            send = _build_payload(step, current)
            print(f"[execute] {step['label']} → POST {step['url']}")
            print(f"[execute] payload: {send}")
            async with httpx.AsyncClient(timeout=15) as h:
                r = await h.post(step["url"], json=send)
            print(f"[execute] response {r.status_code}: {r.text[:200]}")
            body = r.json()
            if r.status_code == 422:
                return {"steps": steps_log, "final": current, "missing": body.get("missing", [])}
            steps_log.append({"label": step["label"], "payload": body, "status": r.status_code})
            current = {**current, **body}

    return {"steps": steps_log, "final": current, "missing": []}


# ── Narrate result ────────────────────────────────────────────────────────────
async def _narrate(final: dict, history: list) -> str:
    msg  = final.get("final_message") or final.get("message", "")
    name = final.get("employee_name", "there")
    status = final.get("status", "")

    prompt = (
        f"HR result for {name}: {status}. Message: {msg}\n"
        f"Write ONE warm natural sentence telling them the outcome. "
        f"No JSON, no field names, plain text only."
    )
    r = await client.chat.completions.create(
        model="gpt-4o",
        messages=history + [{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=80,
    )
    return r.choices[0].message.content.strip()


# ── Main handler ──────────────────────────────────────────────────────────────
async def handle_chat(req: ChatRequest) -> ChatResponse:
    today = date.today()
    sess  = _get_session(req.session_id)

    if sess["done"]:
        _sessions[req.session_id] = {"intent": None, "collected": {}, "history": [], "done": False}
        sess = _sessions[req.session_id]

    sess["history"].append({"role": "user", "content": req.message})

    # Context for GPT
    ctx = f"Today: {today.isoformat()}\n"
    if sess["intent"]:
        ctx += f"Intent: {sess['intent']}\n"
    if sess["collected"]:
        ctx += f"Collected: {json.dumps(sess['collected'])}\n"
    if sess["intent"] and sess["intent"] != "unknown":
        miss = _missing(sess["intent"], sess["collected"])
        if miss:
            ctx += f"Still need: {', '.join(miss)}\n"

    messages = [{"role": "system", "content": SYSTEM + f"\n\n[SESSION]\n{ctx}"}] + sess["history"]

    # GPT call
    r = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=300,
        response_format={"type": "json_object"},
    )
    ai = json.loads(r.choices[0].message.content)

    reply     = ai.get("reply", "How can I help?")
    intent    = ai.get("intent") or sess["intent"]
    extracted = _normalize(ai.get("extracted") or {})
    ready     = bool(ai.get("ready", False))

    print(f"[agent] GPT extracted: {extracted}  ready={ready}  intent={intent}")

    if intent and intent != "unknown":
        sess["intent"] = intent
    sess["collected"].update(extracted)
    sess["history"].append({"role": "assistant", "content": reply})

    print(f"[agent] Session collected: {sess['collected']}")

    # Override ready if fields are actually missing
    if ready and sess["intent"] and sess["intent"] != "unknown":
        miss = _missing(sess["intent"], sess["collected"])
        if miss:
            print(f"[agent] GPT said ready but missing {miss} — overriding")
            ready = False

    if not ready or not sess["intent"] or sess["intent"] == "unknown":
        return ChatResponse(reply=reply, status="collecting", collected=sess["collected"] or None)

    # Resolve dates and execute
    payload = _resolve_dates(dict(sess["collected"]), today)
    print(f"[agent] Final payload for execution: {payload}")

    result = await _execute(sess["intent"], payload)

    if result["missing"]:
        miss_str = ", ".join(result["missing"])
        print(f"[agent] Backend still missing: {miss_str}")
        follow = messages + [
            {"role": "assistant", "content": reply},
            {"role": "user", "content": f"System says still missing: {miss_str}. Ask naturally for just the first one. ready=false."},
        ]
        r2  = await client.chat.completions.create(
            model="gpt-4o", messages=follow, temperature=0.7, max_tokens=120,
            response_format={"type": "json_object"},
        )
        ai2    = json.loads(r2.choices[0].message.content)
        reply2 = ai2.get("reply", f"Just need one more thing — {miss_str}?")
        sess["history"].append({"role": "assistant", "content": reply2})
        return ChatResponse(reply=reply2, status="collecting", collected=sess["collected"] or None)

    summary = await _narrate(result["final"], sess["history"])
    sess["done"] = True
    return ChatResponse(reply=summary, status="done", workflow_result=result, collected=sess["collected"])


def reset_session(session_id: str):
    _sessions.pop(session_id, None)