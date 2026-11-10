from __future__ import annotations

import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .engine import SCENARIOS, STRATEGIES, TASKS, run_case, run_sweep
from .evaluator import overview
from .models import EvalRun, SessionLocal

app = FastAPI(title="轨迹实验室 · 智能体自动化评测", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class RunRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=80)
    scenario: str = Field(min_length=1, max_length=80)
    strategy: str = Field(min_length=1, max_length=80)


class SweepRequest(BaseModel):
    strategy: str = Field(min_length=1, max_length=80)


class ExperimentRequest(BaseModel):
    repetitions: int = Field(default=3, ge=1, le=30)
    strategies: list[str] = Field(default_factory=lambda: list(STRATEGIES), min_length=1, max_length=2)


def get_db():
    with SessionLocal() as session:
        yield session


def serialize(row: EvalRun) -> dict:
    return row.payload


def public_task(task: dict) -> dict:
    return {key: task[key] for key in ("id", "title", "task", "kind")}


def save_run(session: Session, run: dict) -> dict:
    saved = {**run, "id": str(uuid.uuid4())}
    session.add(EvalRun(
        id=saved["id"],
        task_id=saved["task_id"],
        task_title=saved["task_title"],
        scenario=saved["scenario"],
        strategy=saved["strategy"],
        strategy_label=saved["strategy_label"],
        prompt_version=saved["prompt_version"],
        success=saved["success"],
        recovered=saved["recovered"],
        selection_correct=saved["selection_correct"],
        parameter_correct=saved["parameter_correct"],
        execution_ms=saved["execution_ms"],
        created_at=saved["created_at"],
        payload=saved,
    ))
    return saved


def recent(session: Session, limit: int = 10000) -> list[dict]:
    rows = session.scalars(select(EvalRun).order_by(EvalRun.created_at.desc(), EvalRun.id.desc()).limit(limit)).all()
    return [serialize(row) for row in rows]


def summarize_experiment(runs: list[dict]) -> dict:
    strategies = list(dict.fromkeys(run["strategy"] for run in runs))
    return {
        "id": runs[0]["experiment_id"],
        "created_at": min(run["created_at"] for run in runs),
        "repetitions": runs[0]["repetitions"],
        "strategies": strategies,
        "total_runs": len(runs),
        "metrics_by_strategy": {
            strategy: overview([run for run in runs if run["strategy"] == strategy])
            for strategy in strategies
        },
        "scenario_metrics_by_strategy": {
            strategy: {
                scenario["id"]: overview([
                    run for run in runs
                    if run["strategy"] == strategy and run["scenario"] == scenario["id"]
                ])
                for scenario in SCENARIOS
            }
            for strategy in strategies
        },
    }


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "mode": "local-simulator"}


@app.get("/api/tasks")
def list_tasks() -> dict:
    return {"tasks": [public_task(task) for task in TASKS.values()], "scenarios": SCENARIOS, "strategies": STRATEGIES}


@app.get("/api/runs")
def list_runs(session: Session = Depends(get_db)) -> dict:
    return {"runs": recent(session, 100)}


@app.get("/api/experiments")
def list_experiments(session: Session = Depends(get_db)) -> dict:
    grouped: dict[str, list[dict]] = {}
    for run in recent(session):
        experiment_id = run.get("experiment_id")
        if experiment_id:
            grouped.setdefault(experiment_id, []).append(run)
    experiments = [summarize_experiment(items) for items in grouped.values()]
    experiments.sort(key=lambda item: item["created_at"], reverse=True)
    return {"experiments": experiments}


@app.get("/api/experiments/{experiment_id}")
def get_experiment(experiment_id: str, session: Session = Depends(get_db)) -> dict:
    runs = [run for run in recent(session) if run.get("experiment_id") == experiment_id]
    if not runs:
        raise HTTPException(status_code=404, detail="未找到实验批次")
    return {"experiment": summarize_experiment(runs), "runs": runs}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(EvalRun, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="未找到执行记录")
    return {"run": serialize(row)}


@app.get("/api/overview")
def get_overview(session: Session = Depends(get_db)) -> dict:
    return overview(recent(session))


@app.post("/api/run")
async def execute_one(request: RunRequest, session: Session = Depends(get_db)) -> dict:
    try:
        run = await run_case(request.task_id, request.scenario, request.strategy)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    saved = save_run(session, run)
    session.commit()
    return {"run": saved}


@app.post("/api/run-sweep")
async def execute_sweep(request: SweepRequest, session: Session = Depends(get_db)) -> dict:
    if request.strategy not in STRATEGIES:
        raise HTTPException(status_code=422, detail="未知执行策略")
    runs = [save_run(session, run) for run in await run_sweep(request.strategy)]
    session.commit()
    return {"runs": runs, "overview": overview(runs)}


@app.post("/api/experiments")
async def execute_experiment(request: ExperimentRequest, session: Session = Depends(get_db)) -> dict:
    if len(set(request.strategies)) != len(request.strategies):
        raise HTTPException(status_code=422, detail="执行策略不能重复")
    unknown = [strategy for strategy in request.strategies if strategy not in STRATEGIES]
    if unknown:
        raise HTTPException(status_code=422, detail=f"未知执行策略：{', '.join(unknown)}")

    experiment_id = str(uuid.uuid4())
    runs = []
    for repetition in range(1, request.repetitions + 1):
        for strategy in request.strategies:
            for task_id in TASKS:
                for scenario in SCENARIOS:
                    run = await run_case(task_id, scenario["id"], strategy)
                    run.update({
                        "experiment_id": experiment_id,
                        "repetition": repetition,
                        "repetitions": request.repetitions,
                    })
                    runs.append(save_run(session, run))
    session.commit()
    return {"experiment": summarize_experiment(runs), "runs": runs}


@app.get("/api/scenarios")
def list_scenarios() -> dict:
    return {"scenarios": SCENARIOS}
