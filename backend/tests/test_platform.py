import asyncio
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.engine import SCENARIOS, STRATEGIES, TASKS, run_case, run_sweep
from backend.app.evaluator import overview
from backend.app.main import app, get_db, save_run
from backend.app.models import Base, EvalRun


class TestPlatformEngine(unittest.TestCase):
    def run_async(self, task_id: str, scenario: str, strategy: str = "self_correcting"):
        return asyncio.run(run_case(task_id, scenario, strategy))

    def test_normal_call_completes_and_records_correctness(self):
        run = self.run_async("weather_paris", "normal")
        self.assertTrue(run["success"])
        self.assertTrue(run["selection_correct"])
        self.assertTrue(run["parameter_correct"])
        self.assertEqual(len(run["trace"]), 1)

    def test_every_registered_task_has_a_correct_normal_execution(self):
        for task_id, task in TASKS.items():
            with self.subTest(task=task_id):
                run = self.run_async(task_id, "normal")
                self.assertEqual(run["final_result"], task["expected_result"])
                self.assertTrue(run["selection_correct"])
                self.assertTrue(run["parameter_correct"])
                self.assertTrue(run["success"])

    def test_self_correcting_strategy_recovers_all_injected_faults(self):
        for scenario in SCENARIOS:
            if scenario["id"] == "normal":
                continue
            with self.subTest(scenario=scenario["id"]):
                run = self.run_async("convert_km", scenario["id"])
                self.assertTrue(run["success"])
                self.assertTrue(run["recovered"])
                self.assertEqual(run["trace"][-1]["status"], "success")
                self.assertIn(scenario["label"], run["diagnosis"]["evidence"])

    def test_self_correcting_strategy_recovers_faults_for_every_task_type(self):
        for task_id in TASKS:
            for scenario in SCENARIOS:
                if scenario["id"] == "normal":
                    continue
                with self.subTest(task=task_id, scenario=scenario["id"]):
                    run = self.run_async(task_id, scenario["id"])
                    self.assertTrue(run["success"])
                    self.assertTrue(run["recovered"])
                    self.assertEqual(run["selection_correct"], scenario["id"] != "tool_selection_error")
                    self.assertEqual(run["parameter_correct"], scenario["id"] != "invalid_params")

    def test_baseline_does_not_retry_injected_failure(self):
        run = self.run_async("weather_paris", "execution_failure", "baseline")
        self.assertFalse(run["success"])
        self.assertEqual(len(run["trace"]), 1)
        self.assertEqual(run["diagnosis"]["category"], "工具执行异常")

    def test_invalid_task_scenario_and_strategy_are_rejected(self):
        with self.assertRaises(ValueError):
            self.run_async("not-a-task", "normal")
        with self.assertRaises(ValueError):
            self.run_async("weather_paris", "not-a-scenario")
        with self.assertRaises(ValueError):
            self.run_async("weather_paris", "normal", "not-a-strategy")

    def test_full_sweep_has_one_run_per_task_and_scenario(self):
        runs = asyncio.run(run_sweep("baseline"))
        self.assertEqual(len(runs), len(TASKS) * len(SCENARIOS))

    def test_overview_handles_empty_and_calculates_metrics(self):
        self.assertIsNone(overview([])["task_completion_rate"])
        runs = [self.run_async("weather_paris", "normal"), self.run_async("weather_paris", "timeout")]
        metrics = overview(runs)
        self.assertEqual(metrics["total_runs"], 2)
        self.assertEqual(metrics["task_completion_rate"], 1.0)
        self.assertEqual(metrics["fault_recovery_rate"], 1.0)
        self.assertEqual(metrics["fault_recovery_sample_count"], 1)
        self.assertEqual(metrics["completed_run_count"], 2)

    def test_sweep_rejects_unknown_strategy(self):
        with self.assertRaises(ValueError):
            asyncio.run(run_sweep("invalid"))

    def test_run_is_saved_and_queryable(self):
        with TemporaryDirectory() as directory:
            test_engine = create_engine(f"sqlite:///{(Path(directory) / 'runs.sqlite3').as_posix()}")
            Base.metadata.create_all(test_engine)
            run = asyncio.run(run_case("weather_paris", "normal", "baseline"))
            with Session(test_engine) as session:
                saved = save_run(session, run)
                session.commit()
                stored = session.get(EvalRun, saved["id"])
                self.assertEqual(stored.payload["task_id"], "weather_paris")
                self.assertTrue(session.scalars(select(EvalRun)).all()[0].success)
            test_engine.dispose()


class EvaluationApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{(Path(self.temp_directory.name) / 'api-test.sqlite3').as_posix()}")
        Base.metadata.create_all(self.engine)

        def test_session():
            with Session(self.engine, autoflush=False, expire_on_commit=False) as session:
                yield session

        app.dependency_overrides[get_db] = test_session
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()
        self.temp_directory.cleanup()

    def test_health_tasks_and_run_api(self):
        self.assertEqual(self.client.get("/api/health").json()["status"], "ok")
        tasks = self.client.get("/api/tasks").json()["tasks"]
        self.assertGreaterEqual(len(tasks), 2)
        self.assertFalse({"expected_tool", "expected_args", "expected_result"} & tasks[0].keys())
        response = self.client.post("/api/run", json={"task_id": "weather_paris", "scenario": "timeout", "strategy": "self_correcting"})
        self.assertEqual(response.status_code, 200)
        run = response.json()["run"]
        self.assertTrue(run["success"])
        self.assertTrue(run["recovered"])
        self.assertEqual(len(run["trace"]), 2)
        self.assertEqual(self.client.get(f"/api/runs/{run['id']}").json()["run"]["id"], run["id"])
        self.assertEqual(self.client.get("/api/overview").json()["total_runs"], 1)

    def test_run_api_rejects_unknown_scenario(self):
        response = self.client.post("/api/run", json={"task_id": "weather_paris", "scenario": "invalid", "strategy": "baseline"})
        self.assertEqual(response.status_code, 422)

    def test_run_sweep_api_returns_complete_scenario_matrix(self):
        response = self.client.post("/api/run-sweep", json={"strategy": "baseline"})
        self.assertEqual(response.status_code, 200)
        expected_runs = len(TASKS) * len(SCENARIOS)
        self.assertEqual(len(response.json()["runs"]), expected_runs)
        self.assertEqual(response.json()["overview"]["total_runs"], expected_runs)
        self.assertEqual(self.client.get("/api/overview").json()["total_runs"], expected_runs)

    def test_experiment_compares_strategies_and_persists_repetitions(self):
        response = self.client.post("/api/experiments", json={"repetitions": 2})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        expected_runs = 2 * len(TASKS) * len(SCENARIOS) * len(STRATEGIES)
        self.assertEqual(result["experiment"]["total_runs"], expected_runs)
        self.assertEqual(len(result["experiment"]["metrics_by_strategy"]), len(STRATEGIES))
        self.assertTrue(all(run["experiment_id"] == result["experiment"]["id"] for run in result["runs"]))
        self.assertEqual({run["repetition"] for run in result["runs"]}, {1, 2})
        stored = self.client.get("/api/experiments").json()["experiments"]
        self.assertEqual(stored[0]["id"], result["experiment"]["id"])
        details = self.client.get(f"/api/experiments/{result['experiment']['id']}").json()
        self.assertEqual(len(details["runs"]), expected_runs)
        self.assertEqual(len(details["experiment"]["scenario_metrics_by_strategy"]), len(STRATEGIES))

    def test_experiment_rejects_duplicate_or_unknown_strategies(self):
        duplicate = self.client.post("/api/experiments", json={"strategies": ["baseline", "baseline"]})
        unknown = self.client.post("/api/experiments", json={"strategies": ["unknown"]})
        self.assertEqual(duplicate.status_code, 422)
        self.assertEqual(unknown.status_code, 422)


if __name__ == "__main__":
    unittest.main()
