from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import JSON, Boolean, Float, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class EvalRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(80), index=True)
    task_title: Mapped[str] = mapped_column(String(200))
    scenario: Mapped[str] = mapped_column(String(80), index=True)
    strategy: Mapped[str] = mapped_column(String(80), index=True)
    strategy_label: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(120))
    success: Mapped[bool] = mapped_column(Boolean, index=True)
    recovered: Mapped[bool] = mapped_column(Boolean)
    selection_correct: Mapped[bool] = mapped_column(Boolean)
    parameter_correct: Mapped[bool] = mapped_column(Boolean)
    execution_ms: Mapped[float] = mapped_column(Float)
    created_at: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[dict] = mapped_column(JSON)


def _database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(data_dir / 'agent-evaluation-v1.sqlite3').as_posix()}"


DATABASE_URL = _database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base.metadata.create_all(engine)
