from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime, timezone
from typing import Any

TASKS = {
    "weather_paris": {
        "id": "weather_paris",
        "title": "查询巴黎天气",
        "task": "查询巴黎当前的模拟天气。",
        "kind": "weather",
        "expected_tool": "weather_lookup",
        "expected_args": {"city": "巴黎"},
        "expected_result": {"city": "巴黎", "condition": "晴", "temperature_c": 18},
    },
    "weather_tokyo": {
        "id": "weather_tokyo",
        "title": "查询东京天气",
        "task": "查询东京当前的模拟天气。",
        "kind": "weather",
        "expected_tool": "weather_lookup",
        "expected_args": {"city": "东京"},
        "expected_result": {"city": "东京", "condition": "多云", "temperature_c": 21},
    },
    "weather_shanghai": {
        "id": "weather_shanghai",
        "title": "查询上海天气",
        "task": "查询上海当前的模拟天气。",
        "kind": "weather",
        "expected_tool": "weather_lookup",
        "expected_args": {"city": "上海"},
        "expected_result": {"city": "上海", "condition": "小雨", "temperature_c": 19},
    },
    "convert_km": {
        "id": "convert_km",
        "title": "公里换算为米",
        "task": "将 5 公里换算为米。",
        "kind": "unit_conversion",
        "expected_tool": "unit_convert",
        "expected_args": {"value": 5, "from_unit": "km", "to_unit": "m"},
        "expected_result": {"value": 5000, "unit": "m"},
    },
    "convert_m": {
        "id": "convert_m",
        "title": "米换算为公里",
        "task": "将 1250 米换算为公里。",
        "kind": "unit_conversion",
        "expected_tool": "unit_convert",
        "expected_args": {"value": 1250, "from_unit": "m", "to_unit": "km"},
        "expected_result": {"value": 1.25, "unit": "km"},
    },
    "convert_kg": {
        "id": "convert_kg",
        "title": "千克换算为克",
        "task": "将 2.5 千克换算为克。",
        "kind": "unit_conversion",
        "expected_tool": "unit_convert",
        "expected_args": {"value": 2.5, "from_unit": "kg", "to_unit": "g"},
        "expected_result": {"value": 2500, "unit": "g"},
    },
    "convert_seconds": {
        "id": "convert_seconds",
        "title": "秒换算为分钟",
        "task": "将 180 秒换算为分钟。",
        "kind": "unit_conversion",
        "expected_tool": "unit_convert",
        "expected_args": {"value": 180, "from_unit": "s", "to_unit": "min"},
        "expected_result": {"value": 3, "unit": "min"},
    },
    "add_numbers": {
        "id": "add_numbers",
        "title": "计算加法",
        "task": "计算 18 + 24 的结果。",
        "kind": "arithmetic",
        "expected_tool": "calculator",
        "expected_args": {"operation": "add", "left": 18, "right": 24},
        "expected_result": {"value": 42},
    },
    "multiply_numbers": {
        "id": "multiply_numbers",
        "title": "计算乘法",
        "task": "计算 7 * 8 的结果。",
        "kind": "arithmetic",
        "expected_tool": "calculator",
        "expected_args": {"operation": "multiply", "left": 7, "right": 8},
        "expected_result": {"value": 56},
    },
    "divide_numbers": {
        "id": "divide_numbers",
        "title": "计算除法",
        "task": "计算 144 / 12 的结果。",
        "kind": "arithmetic",
        "expected_tool": "calculator",
        "expected_args": {"operation": "divide", "left": 144, "right": 12},
        "expected_result": {"value": 12},
    },
    "subtract_numbers": {
        "id": "subtract_numbers",
        "title": "计算减法",
        "task": "计算 35 - 17 的结果。",
        "kind": "arithmetic",
        "expected_tool": "calculator",
        "expected_args": {"operation": "subtract", "left": 35, "right": 17},
        "expected_result": {"value": 18},
    },
}

SCENARIOS = [
    {"id": "normal", "label": "正常执行", "description": "工具按预期返回结果"},
    {"id": "timeout", "label": "执行超时", "description": "首次调用超过时限"},
    {"id": "empty_result", "label": "空结果", "description": "首次调用返回空内容"},
    {"id": "invalid_params", "label": "参数错误", "description": "首次调用参数不符合工具约束"},
    {"id": "execution_failure", "label": "执行失败", "description": "首次调用抛出模拟异常"},
    {"id": "tool_selection_error", "label": "工具选错", "description": "首次调用选择错误工具"},
]

STRATEGIES = {
    "baseline": {"label": "基线策略", "prompt_version": "baseline-v1", "max_retries": 0},
    "self_correcting": {
        "label": "自纠错策略",
        "prompt_version": "self-correcting-v1",
        "max_retries": 1,
    },
}

TOOL_NAMES = ("weather_lookup", "unit_convert", "calculator")
WEATHER = {
    "巴黎": {"city": "巴黎", "condition": "晴", "temperature_c": 18},
    "东京": {"city": "东京", "condition": "多云", "temperature_c": 21},
    "上海": {"city": "上海", "condition": "小雨", "temperature_c": 19},
}
UNIT_FACTORS = {"km": 1000, "m": 1, "kg": 1000, "g": 1, "s": 1, "min": 60}
UNIT_LABELS = {"公里": "km", "米": "m", "千克": "kg", "克": "g", "秒": "s", "分钟": "min"}

FAULT_DIAGNOSIS = {
    "timeout": ("工具执行超时", "缩短工具执行时间或调整超时预算；确认超时后是否需要安全重试。"),
    "empty_result": ("工具返回空结果", "检查工具返回值约定，并为 null 或空列表设计显式分支。"),
    "invalid_params": ("工具参数错误", "依据工具参数约束校验类型、必填项和取值范围。"),
    "execution_failure": ("工具执行异常", "保留异常类型与调用上下文，并区分可重试和不可重试错误。"),
    "tool_selection_error": ("工具选择错误", "根据任务目标与工具描述重新匹配工具，避免重复提交错误调用。"),
}


def _parse_task(task: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if task["kind"] == "weather":
        match = re.search(r"查询(.+?)当前的模拟天气", task["task"])
        if not match:
            raise ValueError("天气任务文本无法解析")
        return "weather_lookup", {"city": match.group(1)}
    if task["kind"] == "unit_conversion":
        match = re.search(
            r"将\s*([0-9]+(?:\.[0-9]+)?)\s*(公里|米|千克|克|秒|分钟)\s*换算为\s*(公里|米|千克|克|秒|分钟)",
            task["task"],
        )
        if not match:
            raise ValueError("单位换算任务文本无法解析")
        value = float(match.group(1)) if "." in match.group(1) else int(match.group(1))
        return "unit_convert", {
            "value": value,
            "from_unit": UNIT_LABELS[match.group(2)],
            "to_unit": UNIT_LABELS[match.group(3)],
        }
    if task["kind"] == "arithmetic":
        match = re.search(r"计算\s*(-?[0-9]+(?:\.[0-9]+)?)\s*([+*/-])\s*(-?[0-9]+(?:\.[0-9]+)?)\s*的结果", task["task"])
        if not match:
            raise ValueError("算术任务文本无法解析")
        operations = {"+": "add", "-": "subtract", "*": "multiply", "/": "divide"}
        return "calculator", {
            "operation": operations[match.group(2)],
            "left": float(match.group(1)) if "." in match.group(1) else int(match.group(1)),
            "right": float(match.group(3)) if "." in match.group(3) else int(match.group(3)),
        }
    raise ValueError("测试任务没有本地 Agent 规划器")


async def _call_tool(name: str, arguments: dict[str, Any], scenario: str, attempt: int) -> Any:
    inject = attempt == 1
    if name == "weather_lookup":
        city = arguments.get("city")
        if not isinstance(city, str) or not city.strip():
            raise ValueError("city 必须为非空字符串")
        if city not in WEATHER:
            raise ValueError(f"没有城市 {city} 的模拟天气数据")
        if inject and scenario == "timeout":
            await asyncio.sleep(0.12)
        if inject and scenario == "empty_result":
            return []
        if inject and scenario == "execution_failure":
            raise RuntimeError("模拟天气工具执行异常")
        return dict(WEATHER[city])

    if name == "unit_convert":
        value = arguments.get("value")
        source = arguments.get("from_unit")
        target = arguments.get("to_unit")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("value 必须为数字")
        if source not in UNIT_FACTORS or target not in UNIT_FACTORS:
            raise ValueError("不支持的换算单位")
        if (source in {"km", "m"}) != (target in {"km", "m"}) or \
                (source in {"kg", "g"}) != (target in {"kg", "g"}) or \
                (source in {"s", "min"}) != (target in {"s", "min"}):
            raise ValueError("不支持跨量纲换算")
        if inject and scenario == "timeout":
            await asyncio.sleep(0.12)
        if inject and scenario == "empty_result":
            return None
        if inject and scenario == "execution_failure":
            raise RuntimeError("模拟换算工具执行异常")
        converted = round(value * UNIT_FACTORS[source] / UNIT_FACTORS[target], 10)
        return {"value": int(converted) if float(converted).is_integer() else converted, "unit": target}

    if name == "calculator":
        operation = arguments.get("operation")
        left = arguments.get("left")
        right = arguments.get("right")
        if isinstance(left, bool) or not isinstance(left, (int, float)):
            raise ValueError("left 必须为数字")
        if isinstance(right, bool) or not isinstance(right, (int, float)):
            raise ValueError("right 必须为数字")
        if inject and scenario == "timeout":
            await asyncio.sleep(0.12)
        if inject and scenario == "empty_result":
            return None
        if inject and scenario == "execution_failure":
            raise RuntimeError("模拟计算器执行异常")
        if operation == "add":
            value = left + right
        elif operation == "subtract":
            value = left - right
        elif operation == "multiply":
            value = left * right
        elif operation == "divide":
            if right == 0:
                raise ValueError("除数不能为零")
            value = left / right
        else:
            raise ValueError("不支持的算术操作")
        value = round(value, 10)
        return {"value": int(value) if float(value).is_integer() else value}

    raise LookupError(f"未注册的工具：{name}")


def diagnose(scenario: str, selection_correct: bool, parameter_correct: bool, success: bool, trace: list[dict[str, Any]]) -> dict[str, str]:
    if success:
        if scenario == "normal":
            return {"category": "通过", "evidence": "最终结果与预期结果一致。", "suggestion": "保留当前任务、策略与工具配置以支持复现。"}
        first = trace[0]
        scenario_label = next(item["label"] for item in SCENARIOS if item["id"] == scenario)
        evidence = f"首轮注入场景：{scenario_label}；首轮调用状态：{first['status']}；最终结果与预期一致。"
        return {"category": "故障已恢复", "evidence": evidence, "suggestion": "保留失败与恢复两段轨迹，评估该策略在更多重复试验中的稳定性。"}
    if not selection_correct:
        label, suggestion = FAULT_DIAGNOSIS["tool_selection_error"]
        return {"category": label, "evidence": "首次工具调用与任务预期工具不一致。", "suggestion": suggestion}
    if not parameter_correct:
        label, suggestion = FAULT_DIAGNOSIS["invalid_params"]
        return {"category": label, "evidence": "首次调用参数未通过工具输入约束校验。", "suggestion": suggestion}
    label, suggestion = FAULT_DIAGNOSIS.get(scenario, ("任务结果不符合预期", "检查执行轨迹与目标结果定义。"))
    evidence = next((item.get("message", item["status"]) for item in trace if item["attempt"] == 1), "首次调用未获得有效结果。")
    return {"category": label, "evidence": str(evidence), "suggestion": suggestion}


async def run_case(task_id: str, scenario: str, strategy: str) -> dict[str, Any]:
    if task_id not in TASKS:
        raise ValueError("未知测试任务")
    if scenario not in {item["id"] for item in SCENARIOS}:
        raise ValueError("未知故障场景")
    if strategy not in STRATEGIES:
        raise ValueError("未知执行策略")

    task = TASKS[task_id]
    config = STRATEGIES[strategy]
    trace: list[dict[str, Any]] = []
    started = time.perf_counter()
    planned_tool, planned_args = _parse_task(task)
    first_tool = planned_tool
    first_args = dict(planned_args)
    if scenario == "tool_selection_error":
        first_tool = next(name for name in TOOL_NAMES if name != planned_tool)
    if scenario == "invalid_params":
        numeric_key = next(
            (key for key, value in first_args.items() if isinstance(value, (int, float)) and not isinstance(value, bool)),
            None,
        )
        if numeric_key is not None:
            first_args[numeric_key] = "invalid"
        else:
            first_args[next(iter(first_args))] = None
    tool_name = first_tool
    final_result: Any = None

    for attempt in range(1, config["max_retries"] + 2):
        if attempt > 1:
            tool_name, arguments = _parse_task(task)
        else:
            arguments = first_args
        call_started = time.perf_counter()
        try:
            result = await asyncio.wait_for(_call_tool(tool_name, arguments, scenario, attempt), timeout=0.04)
            duration_ms = round((time.perf_counter() - call_started) * 1000, 2)
            if result is None or result == []:
                trace.append({"attempt": attempt, "tool": tool_name, "arguments": arguments, "result": result, "status": "empty_result", "duration_ms": duration_ms, "fault": scenario if attempt == 1 else None, "message": "工具返回空结果"})
                continue
            trace.append({"attempt": attempt, "tool": tool_name, "arguments": arguments, "result": result, "status": "success", "duration_ms": duration_ms, "fault": scenario if attempt == 1 and scenario != "normal" else None, "message": "调用成功"})
            final_result = result
            break
        except asyncio.TimeoutError:
            duration_ms = round((time.perf_counter() - call_started) * 1000, 2)
            trace.append({"attempt": attempt, "tool": tool_name, "arguments": arguments, "result": None, "status": "timeout", "duration_ms": duration_ms, "fault": "timeout", "message": "调用超过 40 ms 时限"})
        except ValueError as exc:
            duration_ms = round((time.perf_counter() - call_started) * 1000, 2)
            trace.append({"attempt": attempt, "tool": tool_name, "arguments": arguments, "result": None, "status": "invalid_params", "duration_ms": duration_ms, "fault": "invalid_params" if attempt == 1 and scenario == "invalid_params" else None, "message": str(exc)})
        except (RuntimeError, LookupError) as exc:
            duration_ms = round((time.perf_counter() - call_started) * 1000, 2)
            status = "execution_failure" if isinstance(exc, RuntimeError) else "tool_selection_error"
            trace.append({"attempt": attempt, "tool": tool_name, "arguments": arguments, "result": None, "status": status, "duration_ms": duration_ms, "fault": scenario if attempt == 1 else None, "message": str(exc)})

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    selection_correct = trace[0]["tool"] == task["expected_tool"]
    parameter_correct = trace[0]["arguments"] == task["expected_args"]
    success = final_result == task["expected_result"]
    recovered = success and scenario != "normal" and len(trace) > 1
    diagnosis = diagnose(scenario, selection_correct, parameter_correct, success, trace)
    return {
        "task_id": task_id,
        "task_title": task["title"],
        "task": task["task"],
        "scenario": scenario,
        "strategy": strategy,
        "strategy_label": config["label"],
        "prompt_version": config["prompt_version"],
        "expected_tool": task["expected_tool"],
        "selection_correct": selection_correct,
        "parameter_correct": parameter_correct,
        "success": success,
        "recovered": recovered,
        "final_result": final_result,
        "expected_result": task["expected_result"],
        "trace": trace,
        "diagnosis": diagnosis,
        "execution_ms": elapsed_ms,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


async def run_sweep(strategy: str) -> list[dict[str, Any]]:
    if strategy not in STRATEGIES:
        raise ValueError("未知执行策略")
    runs = []
    for task_id in TASKS:
        for scenario in SCENARIOS:
            runs.append(await run_case(task_id, scenario["id"], strategy))
    return runs
