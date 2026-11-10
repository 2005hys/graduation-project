from __future__ import annotations

from collections.abc import Iterable


def overview(runs: Iterable[dict]) -> dict:
    runs = list(runs)
    count = len(runs)
    calls = [call for run in runs for call in run["trace"]]
    faulty = [run for run in runs if run["scenario"] != "normal"]
    selection_correct = sum(run["selection_correct"] for run in runs)
    parameter_correct = sum(run["parameter_correct"] for run in runs)
    completed = sum(run["success"] for run in runs)
    recovered = sum(run["recovered"] for run in faulty)
    invalid_calls = sum(call["status"] == "invalid_params" for call in calls)
    return {
        "total_runs": count,
        "tool_selection_correct_count": selection_correct,
        "tool_selection_sample_count": count,
        "tool_selection_accuracy": round(selection_correct / count, 4) if count else None,
        "parameter_correct_count": parameter_correct,
        "parameter_sample_count": count,
        "parameter_correctness": round(parameter_correct / count, 4) if count else None,
        "completed_run_count": completed,
        "task_completion_sample_count": count,
        "task_completion_rate": round(completed / count, 4) if count else None,
        "recovered_run_count": recovered,
        "fault_recovery_sample_count": len(faulty),
        "fault_recovery_rate": round(recovered / len(faulty), 4) if faulty else None,
        "average_execution_ms": round(sum(run["execution_ms"] for run in runs) / count, 2) if count else None,
        "invalid_call_count": invalid_calls,
        "tool_call_count": len(calls),
        "invalid_call_rate": round(invalid_calls / len(calls), 4) if calls else None,
    }
