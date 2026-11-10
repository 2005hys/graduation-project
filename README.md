# 面向工具调用的智能体自动化评测与故障诊断平台

## 项目简介

本项目围绕大语言模型智能体（AI Agent）的工具调用过程，构建可控的自动化评测和故障诊断平台。平台通过确定性本地模拟器执行工具选择、参数生成、工具调用、结果校验与策略重试，注入超时、空结果、参数错误、执行异常和工具误选等场景，保留调用轨迹并计算评测指标。

当前版本为**本地模拟原型**，不调用外部模型。规则模拟器产生的结果仅用于验证平台的测试、指标和诊断流程，不应表述为真实大语言模型性能结论。平台按项目规范采用 Vue 3、Element Plus、ECharts、FastAPI、Pydantic 和 SQLAlchemy；默认使用 SQLite 便于本机启动，可用 `DATABASE_URL` 配置 MySQL。

## 当前已实现

- 十一个确定性任务：三座城市天气查询、四种单位换算、加减乘除各一类。
- 三个本地模拟工具：天气查询、单位换算、计算器；任务规划从任务描述解析参数。
- 六类场景：正常执行、超时、空结果、参数错误、执行失败、工具误选。
- 两种策略：基线（不重试）和自纠错（最多重试一次）。
- 每次调用的工具、参数、结果、状态、注入故障和耗时轨迹。
- 工具选择准确率、参数正确率、任务完成率、故障恢复率、平均耗时和无效调用率。
- 批次实验可对比两种策略，每个任务/场景组合重复 1–30 轮；记录策略、轮次、运行轨迹，并导出完整 JSON 报告。
- 按调用证据展示故障诊断、历史记录、图表和 JSON 导出。
- 后端单元/接口测试使用隔离的临时 SQLite 数据库。

## 指标口径

- **工具选择准确率**：首轮所选工具与任务预期工具一致的运行数 / 运行总数。
- **参数正确率**：首轮参数与该任务预期参数完全一致的运行数 / 运行总数。
- **任务完成率**：最终工具结果与任务预期结果一致的运行数 / 运行总数。
- **故障恢复率**：注入故障后经过后续调用成功完成的运行数 / 非正常场景运行数；正常场景不计入分母。
- **平均执行时间**：每次运行端到端耗时的算术平均值。
- **无效调用率**：参数校验失败的工具调用数 / 工具调用总数。

批次报告同时保存各项指标的分子/样本数。当前模拟器是确定性的，重复轮次用于检查流程可复现性并观察耗时，不代表真实模型的随机波动或统计显著性。

## 环境要求

- Python 3.10 或更新版本
- Node.js 20 或更新版本
- npm

## 本地运行

从项目根目录打开两个终端。

### 终端一：后端

```bash
python -m pip install -r backend/requirements.txt
python -m backend.run
```

后端接口文档地址：`http://127.0.0.1:8000/docs`。

### 终端二：前端

```bash
cd frontend
npm install
npm run dev
```

打开 Vite 提示的本地地址。开发服务器会把 `/api` 请求代理到 `127.0.0.1:8000`。
若默认端口被占用，可通过 `BACKEND_PORT` 设置后端端口，并用 `VITE_API_PROXY_TARGET` 将前端代理指向相同地址。

## 运行测试与构建

```bash
python -m unittest discover -s backend/tests -t . -v
```

```bash
cd frontend
npm run build
```

## API 摘要

- `GET /api/health`：本地服务状态。
- `GET /api/tasks`：任务、场景和策略定义。
- `GET /api/overview`：最近运行汇总指标。
- `GET /api/runs`：最近执行记录。
- `GET /api/runs/{run_id}`：单条执行记录及轨迹。
- `POST /api/run`：运行单项任务。请求字段为 `task_id`、`scenario`、`strategy`。
- `POST /api/run-sweep`：按指定策略运行所有任务和场景组合。
- `GET /api/experiments`：列出已保存的批次摘要。
- `POST /api/experiments`：运行双策略重复实验。可传 `repetitions`（1–30）与 `strategies`（策略 ID 数组，默认两种策略）。
- `GET /api/experiments/{experiment_id}`：读取批次摘要和完整运行轨迹。

模型接入暂不包含在当前原型中。确认模型供应方、预算、数据安全和重试规则后，再为真实 Function Calling 增加适配层，并使用相同任务集和指标进行对照；模拟结果不能当作真实模型性能结论。

## MySQL 配置

设置 `DATABASE_URL` 环境变量，例如：

```text
mysql+pymysql://用户名:密码@主机:3306/数据库名?charset=utf8mb4
```

本地 SQLite 数据库写入 `backend/data/agent-evaluation-v1.sqlite3`。切换至 MySQL 前需自行创建数据库并妥善配置凭据；不要将含真实密码的环境文件提交到版本控制。旧版试运行文件 `backend/data/runs.sqlite3` 会保留，不参与当前原型的数据读取。

## 目录结构

```text
backend/
  __init__.py
  run.py
  app/
    engine.py       # 模拟 Agent、工具执行、场景注入与轨迹
    evaluator.py    # 指标汇总
    main.py         # FastAPI 接口
    models.py       # SQLAlchemy 模型与数据库配置
  tests/            # 单元与接口集成测试
frontend/
  src/
    App.vue         # 评测工作台
    main.js         # Vue 应用入口
    platform.css    # 界面样式
  package.json
  vite.config.js
scripts/
  create_proposal.py        # 生成开题报告雏形
  format_school_proposal.py # 生成学校表格内容版
```

## 开题报告

- `docs/开题报告雏形.docx`：报告正文和排版稿。
- `docs/开题报告-学校表格版.docx`：按学校六项章节结构整理的内容版，包含指标口径与进度安排表；非原 `.doc` 模板的 XML 填充件。
- `scripts/create_proposal.py` 和 `scripts/format_school_proposal.py`：可重新生成文档的脚本。

参考文献候选条目需在提交前通过学校图书馆或正式出版渠道核对作者、版本、卷期和页码；任务书日期、项目类别和导师确认项保持待补。

## 后续工作建议

1. 与导师确认任务书进度节点、评价口径和开题报告模板要求。
2. 扩充并人工审查具有代表性的任务集和工具定义。
3. 在明确模型供应方、预算、数据安全和重试规则后，增加真实 Function Calling 适配器。
4. 进行重复试验和策略对照，报告样本量、随机波动及适用范围。
5. 完善任务配置持久化、模型/提示词版本管理和报告生成。
