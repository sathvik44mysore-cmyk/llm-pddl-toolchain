"""
history.py — Plan history endpoints (per anonymous session).
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.db.crud import get_plan, get_recent_plans, get_session_stats

router = APIRouter(prefix="/api")


def _serialize_plan(plan) -> dict:
    return {
        "id": plan.id,
        "task": plan.task,
        "domain_used": plan.domain_used,
        "plan_cost": plan.plan_cost,
        "solve_time_s": plan.solve_time_s,
        "repaired": plan.repaired,
        "status": plan.status,
        "created_at": plan.created_at.isoformat(),
    }


def _serialize_plan_full(plan) -> dict:
    d = _serialize_plan(plan)
    d.update({
        "domain_pddl": plan.domain_pddl,
        "problem_pddl": plan.problem_pddl,
        "plan_steps": json.loads(plan.plan_steps) if plan.plan_steps else [],
        "explanation": plan.explanation,
    })
    return d


@router.get("/plans")
async def list_plans(request: Request, db: AsyncSession = Depends(get_db)):
    """List recent plans for this session (up to 50)."""
    session_id = request.headers.get("X-Session-ID", "anonymous")
    plans = await get_recent_plans(db, session_id, limit=50)
    return {"plans": [_serialize_plan(p) for p in plans]}


@router.get("/plans/stats")
async def session_stats(request: Request, db: AsyncSession = Depends(get_db)):
    """Aggregate stats for the current session."""
    session_id = request.headers.get("X-Session-ID", "anonymous")
    return await get_session_stats(db, session_id)


@router.get("/plans/{plan_id}")
async def get_plan_detail(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """Get full detail for a single plan."""
    session_id = request.headers.get("X-Session-ID", "anonymous")
    plan = await get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")
    if plan.session_id != session_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    return _serialize_plan_full(plan)
