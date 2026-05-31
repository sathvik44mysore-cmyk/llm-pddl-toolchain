"""
benchmarks.py — Benchmark results endpoints.
"""

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db, AsyncSessionLocal
from api.db.crud import get_all_benchmark_results, save_benchmark_result, clear_benchmark_results

router = APIRouter(prefix="/api")


def _serialize(row) -> dict:
    return {
        "id": row.id,
        "domain_name": row.domain_name,
        "problem_name": row.problem_name,
        "found": row.found,
        "plan_cost": row.plan_cost,
        "solve_time_s": row.solve_time_s,
        "ran_at": row.ran_at.isoformat(),
    }


@router.get("/benchmarks")
async def get_benchmarks(db: AsyncSession = Depends(get_db)):
    """Return all stored benchmark results."""
    rows = await get_all_benchmark_results(db)
    total = len(rows)
    found = sum(1 for r in rows if r.found)
    return {
        "results": [_serialize(r) for r in rows],
        "summary": {
            "total": total,
            "found": found,
            "success_rate": round(found / total * 100) if total else 0,
        },
    }


@router.post("/benchmarks/run")
async def trigger_benchmarks(background_tasks: BackgroundTasks):
    """Kick off a benchmark run in the background."""
    background_tasks.add_task(_run_benchmarks_bg)
    return {"message": "Benchmark run started. Refresh in ~60 seconds to see results."}


async def _run_benchmarks_bg() -> None:
    """Background task: run all benchmark problems and persist results."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from benchmarks.run_benchmarks import run_benchmarks

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, run_benchmarks)

    async with AsyncSessionLocal() as db:
        await clear_benchmark_results(db)
        for r in results:
            await save_benchmark_result(
                db,
                domain_name=r["domain_name"],
                problem_name=r["problem_name"],
                found=r["found"],
                plan_cost=r["plan_cost"],
                solve_time_s=r["solve_time_s"],
            )
        await db.commit()
