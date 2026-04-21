from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/demo/wfh", tags=["WFH Demo"])

# Mock database
EMPLOYEES = {
    "EMP001": {"name": "Alice", "wfh_balance": 5, "leave_balance": 10},
    "EMP002": {"name": "Bob",   "wfh_balance": 0, "leave_balance": 8},
}

def _missing(*fields):
    """Return a standardised missing-fields error response."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "missing_fields",
            "missing": list(fields),
            "message": f"Required fields missing: {', '.join(fields)}",
        },
    )


# ── WFH endpoints ────────────────────────────────────────────────────────────

@router.post("/check")
async def check_wfh_eligibility(payload: dict):
    emp_id = payload.get("emp_id")
    date   = payload.get("date")

    missing = [f for f, v in [("emp_id", emp_id), ("date", date)] if not v]
    if missing:
        return _missing(*missing)

    emp = EMPLOYEES.get(emp_id)
    if not emp:
        return JSONResponse(status_code=404, content={"error": "employee_not_found", "emp_id": emp_id})

    result = dict(payload)
    result["employee_name"] = emp["name"]
    if emp["wfh_balance"] > 0:
        result["is_eligible"] = "yes"
        result["balance"]     = emp["wfh_balance"]
        result["message"]     = f"{emp['name']} is eligible. {emp['wfh_balance']} WFH days remaining."
    else:
        result["is_eligible"] = "no"
        result["message"]     = f"{emp['name']} has no WFH balance remaining."
    return result


@router.post("/apply")
async def apply_wfh(payload: dict):
    emp_id = payload.get("emp_id")
    date   = payload.get("date")

    missing = [f for f, v in [("emp_id", emp_id), ("date", date)] if not v]
    if missing:
        return _missing(*missing)

    emp = EMPLOYEES.get(emp_id)
    if not emp:
        return JSONResponse(status_code=404, content={"error": "employee_not_found", "emp_id": emp_id})

    emp["wfh_balance"] -= 1
    payload["status"]        = "APPROVED"
    payload["employee_name"] = emp["name"]
    payload["final_message"] = (
        f"WFH approved for {emp['name']} on {date}. "
        f"Remaining WFH balance: {emp['wfh_balance']} day(s)."
    )
    return payload


@router.post("/reject")
async def reject_wfh(payload: dict):
    emp_id = payload.get("emp_id", "unknown")
    emp    = EMPLOYEES.get(emp_id, {})
    payload["status"]        = "REJECTED"
    payload["employee_name"] = emp.get("name", emp_id)
    payload["final_message"] = (
        f"WFH request rejected for {emp.get('name', emp_id)}: insufficient balance."
    )
    return payload


# ── Leave endpoints ───────────────────────────────────────────────────────────

@router.post("/leave/check")
async def check_leave_eligibility(payload: dict):
    emp_id    = payload.get("emp_id")
    from_date = payload.get("from_date")
    to_date   = payload.get("to_date")
    reason    = payload.get("reason")

    missing = [f for f, v in [
        ("emp_id", emp_id), ("from_date", from_date),
        ("to_date", to_date), ("reason", reason),
    ] if not v]
    if missing:
        return _missing(*missing)

    emp = EMPLOYEES.get(emp_id)
    if not emp:
        return JSONResponse(status_code=404, content={"error": "employee_not_found", "emp_id": emp_id})

    result = dict(payload)
    result["employee_name"] = emp["name"]
    if emp["leave_balance"] > 0:
        result["is_eligible"] = "yes"
        result["balance"]     = emp["leave_balance"]
        result["message"]     = f"{emp['name']} is eligible. {emp['leave_balance']} leave days remaining."
    else:
        result["is_eligible"] = "no"
        result["message"]     = f"{emp['name']} has no leave balance."
    return result


@router.post("/leave/apply")
async def apply_leave(payload: dict):
    emp_id    = payload.get("emp_id")
    from_date = payload.get("from_date")
    to_date   = payload.get("to_date")
    reason    = payload.get("reason")

    missing = [f for f, v in [
        ("emp_id", emp_id), ("from_date", from_date),
        ("to_date", to_date), ("reason", reason),
    ] if not v]
    if missing:
        return _missing(*missing)

    emp = EMPLOYEES.get(emp_id)
    if not emp:
        return JSONResponse(status_code=404, content={"error": "employee_not_found", "emp_id": emp_id})

    emp["leave_balance"] -= 1
    payload["status"]        = "APPROVED"
    payload["employee_name"] = emp["name"]
    payload["final_message"] = (
        f"Leave approved for {emp['name']} from {from_date} to {to_date} "
        f"({reason}). Remaining leave: {emp['leave_balance']} day(s)."
    )
    return payload


@router.post("/leave/reject")
async def reject_leave(payload: dict):
    emp_id = payload.get("emp_id", "unknown")
    emp    = EMPLOYEES.get(emp_id, {})
    payload["status"]        = "REJECTED"
    payload["employee_name"] = emp.get("name", emp_id)
    payload["final_message"] = (
        f"Leave request rejected for {emp.get('name', emp_id)}: insufficient balance."
    )
    return payload