from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from finspoly_commons import NotFoundError

from ..models import RuleCreate, ScoreRequest, ScoreResponse
from ..services import FraudScorer, get_scorer

router = APIRouter(prefix="/v1", tags=["scoring"])


@router.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest, scorer: FraudScorer = Depends(get_scorer)) -> ScoreResponse:
    return scorer.score(req)


@router.get("/scores/{txn_id}", response_model=ScoreResponse)
def get_score(txn_id: str, scorer: FraudScorer = Depends(get_scorer)) -> ScoreResponse:
    found = scorer.get_score(txn_id)
    if not found:
        raise NotFoundError(f"score for txn {txn_id} not found")
    return found


@router.get("/rules")
def list_rules(scorer: FraudScorer = Depends(get_scorer)):
    return scorer.list_rules()


@router.post("/rules")
def add_rule(body: RuleCreate, scorer: FraudScorer = Depends(get_scorer)):
    return scorer.add_rule(name=body.name, kind=body.kind, threshold=body.threshold, enabled=body.enabled)


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
