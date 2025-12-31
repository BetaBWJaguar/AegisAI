from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from security.breach.infraction.infractionserviceimpl import InfractionServiceImpl

router = APIRouter()
service = InfractionServiceImpl()


class InfractionRequest(BaseModel):
    text: str


@router.post("/analyze")
def analyze_infraction(req: InfractionRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    result = service.analyze(req.text)
    decision = result.decision

    return {
        "violation": result.is_violation,
        "riskTier": result.risk_tier,
        "score": round(result.score, 4),
        "action": decision.action,
        "notifyUser": decision.notify_user,
        "notifyAdmin": decision.notify_admin,
        "maskContent": decision.mask_content,
        "logEvent": decision.log_event,
        "reason": decision.reason,
        "details": result.details
    }


@router.post("/risk-tier")
def analyze_risk_tier(req: InfractionRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    risk_tier, score, is_violation = service.analyze_risk(req.text)

    return {
        "violation": is_violation,
        "riskTier": risk_tier,
        "score": round(score, 4)
    }


@router.post("/decision")
def analyze_decision(req: InfractionRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    decision = service.decide_action(req.text)

    return {
        "action": decision.action,
        "notifyUser": decision.notify_user,
        "notifyAdmin": decision.notify_admin,
        "maskContent": decision.mask_content,
        "logEvent": decision.log_event,
        "reason": decision.reason
    }

