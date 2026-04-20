from fastapi import APIRouter

router = APIRouter(prefix="/api/demo/wfh", tags=["WFH Demo"])

# Mock Database
EMPLOYEES = {
    "EMP001": {"name": "Alice", "wfh_balance": 5},
    "EMP002": {"name": "Bob", "wfh_balance": 0},
}

@router.post("/check")
async def check_eligibility(payload: dict):
    """Checks if the employee has WFH balance."""
    emp_id = payload.get("emp_id")
    emp = EMPLOYEES.get(emp_id)
    
    # We copy the payload to preserve the original data for the next node
    result = dict(payload)
    
    if emp and emp["wfh_balance"] > 0:
        result["is_eligible"] = "yes"
        result["balance"] = emp["wfh_balance"]
        result["message"] = f"Eligible. {emp['wfh_balance']} days left."
    else:
        result["is_eligible"] = "no"
        result["message"] = "Not eligible or zero balance."
        
    return result

@router.post("/apply")
async def apply_wfh(payload: dict):
    """Final API to actually deduct the WFH balance."""
    emp_id = payload.get("emp_id")
    emp = EMPLOYEES.get(emp_id)
    
    if emp:
        emp["wfh_balance"] -= 1  # Deduct balance
        payload["status"] = "APPROVED"
        payload["final_message"] = f"WFH approved for {payload.get('date')}. Remaining balance: {emp['wfh_balance']}."
    
    return payload

@router.post("/reject")
async def reject_wfh(payload: dict):
    """API to handle rejections."""
    payload["status"] = "REJECTED"
    payload["final_message"] = "Your WFH request was automatically rejected due to insufficient balance."
    return payload