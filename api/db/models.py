"""
ORM models for PlanForge.

Phase 1: no authentication — plans are identified by an anonymous session_id.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from api.db.database import Base


class Plan(Base):
    """Stores a single AI-generated plan and all associated PDDL artifacts."""

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Anonymous session identifier (Phase 1 — no auth)
    session_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Original natural-language task supplied by the user
    task: Mapped[str] = mapped_column(String, nullable=False)

    # PDDL artifacts
    domain_pddl: Mapped[str] = mapped_column(Text, nullable=False)
    problem_pddl: Mapped[str] = mapped_column(Text, nullable=False)

    # JSON array of action strings, e.g. '["(move a b)", "(pick c)"]'
    plan_steps: Mapped[str] = mapped_column(Text, nullable=False)

    # Plain-English explanation of the plan
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    # Name of the domain library entry used, or 'generated'
    domain_used: Mapped[str] = mapped_column(String, nullable=False)

    # Number of plan steps (plan cost)
    plan_cost: Mapped[int] = mapped_column(Integer, nullable=False)

    # Planner wall-clock time in seconds
    solve_time_s: Mapped[float] = mapped_column(Float, nullable=False)

    # Whether the plan required an automated repair pass
    repaired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 'success' | 'failed'
    status: Mapped[str] = mapped_column(String, nullable=False, default="success")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), default=datetime.utcnow
    )


class BenchmarkResult(Base):
    """Result of running Fast Downward on a hand-written benchmark problem."""

    __tablename__ = "benchmark_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    problem_name: Mapped[str] = mapped_column(String, nullable=False)
    found: Mapped[bool] = mapped_column(Boolean, nullable=False)
    plan_cost: Mapped[int] = mapped_column(Integer, nullable=True)
    solve_time_s: Mapped[float] = mapped_column(Float, nullable=True)
    ran_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), default=datetime.utcnow
    )


class Domain(Base):
    """A reusable PDDL domain stored in the library."""

    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Unique human-readable identifier for the domain
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    description: Mapped[str] = mapped_column(Text, nullable=True)

    domain_pddl: Mapped[str] = mapped_column(Text, nullable=False)

    # 'builtin' | 'generated' | 'user'
    source: Mapped[str] = mapped_column(String, nullable=False, default="builtin")

    # How many times this domain has been used to generate a plan
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), default=datetime.utcnow
    )
