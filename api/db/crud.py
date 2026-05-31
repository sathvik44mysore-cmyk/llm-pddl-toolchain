"""
Async CRUD helpers for PlanForge.

All functions accept an AsyncSession as their first argument and are safe
to call from FastAPI path operations or background tasks.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import BenchmarkResult, Domain, Plan


# ---------------------------------------------------------------------------
# Plan helpers
# ---------------------------------------------------------------------------


async def create_plan(
    db: AsyncSession,
    *,
    task: str,
    domain_pddl: str,
    problem_pddl: str,
    plan_steps: list,
    explanation: str,
    domain_used: str,
    plan_cost: int,
    solve_time_s: float,
    repaired: bool,
    status: str,
    session_id: str,
) -> Plan:
    """Persist a new plan record and return it with its generated id."""
    plan = Plan(
        session_id=session_id,
        task=task,
        domain_pddl=domain_pddl,
        problem_pddl=problem_pddl,
        plan_steps=json.dumps(plan_steps),
        explanation=explanation,
        domain_used=domain_used,
        plan_cost=plan_cost,
        solve_time_s=solve_time_s,
        repaired=repaired,
        status=status,
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


async def get_plan(db: AsyncSession, plan_id: int) -> Optional[Plan]:
    """Return a plan by primary key, or None if not found."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    return result.scalar_one_or_none()


async def get_recent_plans(
    db: AsyncSession, session_id: str, limit: int = 20
) -> list[Plan]:
    """Return the most recent plans for a given anonymous session."""
    result = await db.execute(
        select(Plan)
        .where(Plan.session_id == session_id)
        .order_by(Plan.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Domain helpers
# ---------------------------------------------------------------------------


async def get_all_domains(db: AsyncSession) -> list[Domain]:
    """Return all domains ordered alphabetically by name."""
    result = await db.execute(select(Domain).order_by(Domain.name))
    return list(result.scalars().all())


async def get_domain_by_name(db: AsyncSession, name: str) -> Optional[Domain]:
    """Return a domain by its unique name, or None if not found."""
    result = await db.execute(select(Domain).where(Domain.name == name))
    return result.scalar_one_or_none()


async def create_domain(
    db: AsyncSession,
    *,
    name: str,
    description: str,
    domain_pddl: str,
    source: str = "builtin",
) -> Domain:
    """Create and persist a new domain entry."""
    domain = Domain(
        name=name,
        description=description,
        domain_pddl=domain_pddl,
        source=source,
    )
    db.add(domain)
    await db.flush()
    await db.refresh(domain)
    return domain


async def increment_domain_use_count(db: AsyncSession, name: str) -> None:
    """Atomically increment the use_count for the domain with the given name."""
    await db.execute(
        update(Domain)
        .where(Domain.name == name)
        .values(use_count=Domain.use_count + 1)
    )


async def count_plans_today(db: AsyncSession, session_id: str) -> int:
    """Count successful plans created today (UTC) for a given session."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(Plan.id))
        .where(Plan.session_id == session_id)
        .where(Plan.created_at >= today_start)
        .where(Plan.status == "success")
    )
    return result.scalar_one() or 0


async def get_session_stats(db: AsyncSession, session_id: str) -> dict:
    """Aggregate stats for a session: total, success count, favourite domain."""
    result = await db.execute(
        select(Plan).where(Plan.session_id == session_id).order_by(Plan.created_at.desc())
    )
    plans = list(result.scalars().all())
    total = len(plans)
    successes = [p for p in plans if p.status == "success"]
    domain_counts: dict[str, int] = {}
    for p in successes:
        domain_counts[p.domain_used] = domain_counts.get(p.domain_used, 0) + 1
    favourite = max(domain_counts, key=domain_counts.get) if domain_counts else None
    avg_steps = round(sum(p.plan_cost for p in successes) / len(successes), 1) if successes else 0
    return {
        "total": total,
        "successful": len(successes),
        "success_rate": round(len(successes) / total * 100) if total else 0,
        "favourite_domain": favourite,
        "avg_steps": avg_steps,
    }


# ---------------------------------------------------------------------------
# Benchmark helpers
# ---------------------------------------------------------------------------


async def save_benchmark_result(
    db: AsyncSession,
    *,
    domain_name: str,
    problem_name: str,
    found: bool,
    plan_cost: Optional[int],
    solve_time_s: float,
) -> BenchmarkResult:
    """Persist a single benchmark result."""
    row = BenchmarkResult(
        domain_name=domain_name,
        problem_name=problem_name,
        found=found,
        plan_cost=plan_cost,
        solve_time_s=solve_time_s,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def get_all_benchmark_results(db: AsyncSession) -> list[BenchmarkResult]:
    """Return all benchmark results ordered by domain then problem."""
    result = await db.execute(
        select(BenchmarkResult).order_by(BenchmarkResult.domain_name, BenchmarkResult.problem_name)
    )
    return list(result.scalars().all())


async def clear_benchmark_results(db: AsyncSession) -> None:
    """Delete all stored benchmark results before a fresh run."""
    await db.execute(delete(BenchmarkResult))
