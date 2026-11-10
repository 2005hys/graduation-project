from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "开题报告雏形.docx"

REFERENCES = [
    "Yao S, Zhao J, Yu D, et al. ReAct: Synergizing Reasoning and Acting in Language Models[C]//International Conference on Learning Representations (ICLR). 2023. arXiv:2210.03629.",
    "Schick T, Dwivedi-Yu J, Dessì R, et al. Toolformer: Language Models Can Teach Themselves to Use Tools[C]//Advances in Neural Information Processing Systems (NeurIPS). 2023. arXiv:2302.04761.",
    "Qiao et al. API-Bank: A Comprehensive Benchmark for Tool-Augmented LLMs[C]//Findings of the Association for Computational Linguistics: EMNLP. 2023. arXiv:2304.08244.",
    "Qin Y, Liang S, Ye Y, et al. ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs[C]//International Conference on Learning Representations (ICLR). 2024. arXiv:2307.16789.",
    "Liu X, Yu H, Zhang H, et al. AgentBench: Evaluating LLMs as Agents[C]//International Conference on Learning Representations (ICLR). 2024. arXiv:2308.03688.",
    "Ruan Y, Dong H, Wang A, et al. Identifying the Risks of LM Agents with an LM-Emulated Sandbox[C]//International Conference on Learning Representations (ICLR). 2024. arXiv:2309.15817.",
    "Yao S, Chen H, Yang J, et al. τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains[EB/OL]. 2024. arXiv:2406.12045.",
    "Debenedetti E, Zhang J, Balunović M, et al. AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents[EB/OL]. 2024. arXiv:2406.13352.",
    "Lu J, et al. ToolSandbox: A Stateful, Conversational, Interactive Evaluation Benchmark for LLM Tool Use[EB/OL]. 2024. arXiv:2408.04682.",
    "Deng X, Gu Y, Zheng B, et al. Mind2Web: Towards a Generalist Agent for the Web[C]//Advances in Neural Information Processing Systems (NeurIPS). 2023. arXiv:2306.06070.",
    "Zhou S, Xu F F, Zhu H, et al. WebArena: A Realistic Web Environment for Building Autonomous Agents[C]//International Conference on Learning Representations (ICLR). 2024. arXiv:2307.13854.",
    "Xie T, Zhang D, Chen J, et al. OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments[C]//Advances in Neural Information Processing Systems (NeurIPS). 2024. arXiv:2404.07972.",
    "Mialon G, Fourrier C, Swift C, et al. GAIA: A Benchmark for General AI Assistants[C]//International Conference on Learning Representations (ICLR). 2024. arXiv:2311.12983.",
    "Xi Z, Chen W, Guo X, et al. The Rise and Potential of Large Language Model Based Agents: A Survey[EB/OL]. 2023. arXiv:2309.07864.",
    "Wang L, Ma C, Feng X, et al. A Survey on Large Language Model Based Autonomous Agents[EB/OL]. 2023. arXiv:2308.11432.",
    "Patil S G, Zhang T, Wang X, et al. Gorilla: Large Language Model Connected with Massive APIs[EB/OL]. 2023. arXiv:2305.15334.",
    "Khot T, Trivedi H, Finlayson M, et al. Decomposed Prompting: A Modular Approach for Solving Complex Tasks[C]//International Conference on Learning Representations (ICLR). 2023. arXiv:2210.02406.",
    "Sumers T R, Yao S, Narasimhan K, et al. Cognitive Architectures for Language Agents[EB/OL]. 2023. arXiv:2309.02427.",
    "ISO/IEC. ISO/IEC 25010:2023 Systems and Software Engineering—Systems and Software Quality Requirements and Evaluation (SQuaRE)—Product Quality Model[S]. Geneva: International Organization for Standardization, 2023.",
    "ISO/IEC/IEEE. ISO/IEC/IEEE 29119-1:2022 Software and Systems Engineering—Software Testing—Part 1: General Concepts[S]. Geneva: International Organization for Standardization, 2022.",
    "ISO/IEC/IEEE. ISO/IEC/IEEE 29119-2:2021 Software and Systems Engineering—Software Testing—Part 2: Test Processes[S]. Geneva: International Organization for Standardization, 2021.",
    "National Institute of Standards and Technology. Artificial Intelligence Risk Management Framework (AI RMF 1.0)[R]. NIST AI 100-1. 2023. DOI:10.6028/NIST.AI.100-1.",
]


def set_cell_shading(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    properties.append(shading)


def set_cell_text(cell, value: str, bold: bool = False) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(value)
    run.bold = bold
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(10)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_repeat_table_header(row) -> None:
    properties = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    properties.append(repeat)


def set_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, end])


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.3)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.5)
    section.header_distance = Cm(1.3)
    section.footer_distance = Cm(1.2)

    normal = document.styles["Normal"]
    normal.font.name = "宋体"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor(34, 43, 49)
    normal.paragraph_format.line_spacing = 1.45
    normal.paragraph_format.space_after = Pt(5)
    for style_name, size, color in [("Heading 1", 15, "183743"), ("Heading 2", 12, "267C7B")]:
        style = document.styles[style_name]
        style.font.name = "黑体"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(13)
        style.paragraph_format.space_after = Pt(6)
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_run = header.add_run("武汉大学本科毕业论文（设计）开题报告 · 雏形")
    header_run.font.size = Pt(8)
    header_run.font.color.rgb = RGBColor(125, 139, 140)
    footer = section.footer.paragraphs[0]
    set_page_number(footer)


def add_paragraph(document: Document, text: str, first_line: bool = True) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if first_line:
        paragraph.paragraph_format.first_line_indent = Cm(0.74)
    paragraph.paragraph_format.widow_control = True
    paragraph.add_run(text)


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    configure_document(document)

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(8)
    title.paragraph_format.space_after = Pt(7)
    run = title.add_run("武汉大学本科毕业论文（设计）开题报告")
    run.bold = True
    run.font.name = "黑体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    run.font.size = Pt(19)
    run.font.color.rgb = RGBColor(24, 55, 67)

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(15)
    subrun = subtitle.add_run("（雏形稿 · 请导师审阅后按学院模板定稿）")
    subrun.font.size = Pt(9)
    subrun.font.color.rgb = RGBColor(125, 139, 140)

    info = document.add_table(rows=3, cols=4)
    info.alignment = WD_TABLE_ALIGNMENT.CENTER
    info.autofit = False
    widths = [Cm(2.1), Cm(5.2), Cm(2.1), Cm(5.2)]
    for row in info.rows:
        for index, cell in enumerate(row.cells):
            cell.width = widths[index]
    values = [
        ["学生姓名", "侯玉生", "学号", "2023302111225"],
        ["学院", "计算机学院", "专业", "软件工程"],
        ["指导教师", "刘进（教授）", "题目类别", "待确认"],
    ]
    for row_index, row_values in enumerate(values):
        for col_index, value in enumerate(row_values):
            cell = info.cell(row_index, col_index)
            set_cell_text(cell, value, col_index % 2 == 0)
            if col_index % 2 == 0:
                set_cell_shading(cell, "EAF1EF")

    project_title = document.add_paragraph()
    project_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    project_title.paragraph_format.space_before = Pt(13)
    project_title.paragraph_format.space_after = Pt(16)
    title_run = project_title.add_run("面向工具调用的智能体自动化评测与故障诊断平台设计与实现")
    title_run.bold = True
    title_run.font.name = "黑体"
    title_run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    title_run.font.size = Pt(15)

    document.add_heading("1. 选题目的和意义", level=1)
    add_paragraph(document, "随着大语言模型从文本问答扩展到能够调用外部工具的智能体，模型需要根据任务选择工具、生成结构化参数、理解工具返回并决定后续行动。工具调用扩大了智能体可完成任务的范围，也引入了新的失效路径：工具误选、参数不符合约束、执行超时、空结果、服务异常以及多步任务最终结果偏离目标。仅以最终答案正确与否衡量系统，难以定位故障发生的位置，也难以比较不同纠错策略的作用。")
    add_paragraph(document, "本课题拟设计并实现一个面向工具调用流程的自动化评测与故障诊断平台。平台围绕任务、工具、执行策略、故障场景和运行记录建立统一实验流程，保存每次调用的工具、参数、返回值、状态、耗时及诊断证据，并据此计算工具选择准确率、参数正确率、任务完成率、异常恢复率、平均执行时间和无效调用率。研究目标不是宣称提出通用智能体算法，而是构建可控、可重复、可解释的实验支撑环境，为工具调用可靠性分析提供工程基础。")
    add_paragraph(document, "课题的理论意义在于将智能体的工具规划与软件测试中的输入约束、故障注入、轨迹观测和覆盖分析联系起来，探索从单一端到端成功率向过程级评价与证据驱动诊断扩展的可行方法。实践意义在于帮助开发者复现工具调用失效、比较基线与自纠错策略，并形成可以重复运行的评测记录和报告。该平台的实验结论仅对明确给出的任务集、工具模拟器与配置成立，后续需要通过真实模型和更多样本验证外部有效性。")

    document.add_heading("2. 国内外研究现状和发展趋势", level=1)
    document.add_heading("2.1 国外研究现状", level=2)
    add_paragraph(document, "工具增强语言模型研究从模型自主决定何时调用工具逐渐发展到多步交互、环境状态管理与安全性测试。ReAct 将推理与行动交替组织，使工具调用轨迹成为可观察的过程；Toolformer 探索模型通过自监督数据学习调用工具；API-Bank、ToolLLM 等工作构建工具/API 使用任务和评测方法，为工具选择、调用生成及结果利用提供基准[1-4]。这些工作说明，评测对象不应只限于最终文本，还应覆盖中间动作与工具接口行为。")
    add_paragraph(document, "在通用智能体评价方面，AgentBench、GAIA 等基准将评测扩展至多环境、多步骤任务；Mind2Web、WebArena 与 OSWorld 分别以网页或桌面环境检验智能体在交互状态中的行动表现[5,10-13]。ToolEmu 通过模拟环境研究工具使用风险，τ-bench 强调工具、智能体与用户在真实业务规则下的多轮交互；ToolSandbox 强调有状态、对话式的工具使用评测；AgentDojo 则关注动态环境中的提示注入与防御[6-9]。这些研究共同反映出评测正在由静态单轮问答走向动态环境、过程轨迹、规则遵循与风险鲁棒性分析。")
    add_paragraph(document, "已有综述从自主智能体的组成、规划、记忆、工具使用和评测等角度归纳了技术路线[14-15,18]；Gorilla 等工作关注模型与大量 API 的连接能力[16]。总体而言，当前研究仍面临基准任务与真实应用分布差异、工具返回随机性、失败标签粒度不一致、恢复策略难以公平比较和实验复现信息不足等问题。不同论文的任务、模型、提示词和评分规则差异明显，跨基准分数不宜直接横向比较。")
    document.add_heading("2.2 国内相关工作与发展趋势", level=2)
    add_paragraph(document, "国内团队参与了工具增强模型、API 调用数据和智能体基准研究，例如 API-Bank 与 ToolLLM/ToolBench 等工作面向工具使用能力构建了数据、工具接口或评测流程[3-4]。当前可观察到的研究趋势包括：从封闭任务集合扩展到可组合工具和状态化环境；由成功率扩展到参数正确性、过程遵循、效率、安全性与鲁棒性等多维指标；由单次测试转向多次重复和配置留存；由结果打分转向根据执行证据解释错误。国内外文献中任务定义和术语并不完全统一，因此本课题将先对指标定义、分母口径和诊断标签作操作化说明，并在实现中保持配置与执行轨迹可导出。")

    document.add_heading("3. 研究内容、研究方法、技术路线及可行性分析", level=1)
    document.add_heading("3.1 研究内容", level=2)
    for text in [
        "（1）需求分析与实验对象建模：定义测试任务、工具接口及参数约束、执行策略、故障场景和运行记录的数据结构。",
        "（2）工具调用执行与故障注入：实现本地模拟 Agent 的任务解析、工具选择、参数生成、工具执行、结果检查和有限重试；支持正常执行、超时、空结果、参数错误、执行失败及工具误选等场景。",
        "（3）执行轨迹与数据持久化：逐次记录任务文本、预期工具及结果、实际工具与参数、工具返回、故障状态、耗时、重试和最终完成状态，支持历史查询和 JSON 导出。",
        "（4）自动化评测与故障诊断：明确指标公式和统计口径，依据调用状态、参数校验、工具选择及最终结果分类故障，展示证据与改进建议。",
        "（5）可视化平台及对照实验：开发任务/场景/策略选择、单次执行、批量全场景运行、结果概览、完成率图表和轨迹记录界面；对比不重试的基线策略与有限次自纠错策略。",
        "（6）实验分析与论文撰写：固定任务和模拟器版本，设计重复实验和配置记录，分析各故障类型下的完成率、恢复率、无效调用率及耗时差异，并说明实验边界。",
    ]:
        add_paragraph(document, text, first_line=False)

    document.add_heading("3.2 研究方法", level=2)
    add_paragraph(document, "文献研究法：梳理工具增强语言模型、智能体基准、软件测试与质量评价相关工作，提炼适用于本课题的测试对象、故障类型和评价维度。")
    add_paragraph(document, "原型设计与软件工程方法：以模块化方式实现任务管理、工具模拟器、Agent 执行器、轨迹存储、评测器、诊断器和可视化界面；通过单元测试及接口测试检查核心路径。")
    add_paragraph(document, "控制变量实验法：固定任务集合、工具定义、模拟器版本和场景参数，比较基线与自纠错策略；记录提示词/策略版本、配置和运行数据，避免在分析中混淆策略差异与环境差异。")
    add_paragraph(document, "定量分析法：按预先定义的分子、分母统计各项指标，使用描述性统计对比不同策略和故障场景；如后续接入大语言模型，应进行多次独立重复，报告样本量与波动范围，并将随机性、模型版本和调用参数纳入配置。")

    document.add_heading("3.3 指标定义（初拟，需导师确认）", level=2)
    metric_table = document.add_table(rows=1, cols=3)
    metric_table.style = "Table Grid"
    metric_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, value in zip(metric_table.rows[0].cells, ["指标", "初拟计算口径", "说明"]):
        set_cell_text(cell, value, True)
        set_cell_shading(cell, "EAF1EF")
    set_repeat_table_header(metric_table.rows[0])
    metrics = [
        ("工具选择准确率", "首轮实际工具正确的任务数 / 任务总数", "以首轮为准，故障注入的误选单独标注。"),
        ("参数正确率", "首轮参数符合预期约束的调用数 / 首轮调用总数", "参数比较按工具定义的字段、类型及取值规则。"),
        ("任务完成率", "最终结果满足预期条件的任务数 / 任务总数", "成功判定使用任务级预期结果。"),
        ("异常恢复率", "注入故障后恢复完成的任务数 / 可恢复故障任务数", "不可恢复故障及无故障样本不计入分母。"),
        ("平均执行时间", "任务端到端执行耗时总和 / 任务数", "拆分记录调用时延和总耗时。"),
        ("无效调用率", "未通过工具约束的调用次数 / 工具调用总次数", "统计所有尝试，不仅首轮。"),
    ]
    for metric in metrics:
        cells = metric_table.add_row().cells
        for cell, value in zip(cells, metric):
            set_cell_text(cell, value)
    for row in metric_table.rows:
        for cell, width in zip(row.cells, [Cm(3.1), Cm(7.2), Cm(5.1)]):
            cell.width = width

    document.add_heading("3.4 技术路线", level=2)
    add_paragraph(document, "课题资料分析与需求确认 → 定义任务、工具、指标和故障模型 → 实现模拟 Agent 与可控工具环境 → 接入轨迹与持久化层 → 实现自动评测和基于规则/证据的诊断 → 构建前端配置与可视化界面 → 进行单元测试、接口测试与对照实验 → 分析结果、完善系统并撰写论文。")
    add_paragraph(document, "平台按前后端分离设计：前端采用 Vue 3、Element Plus 和 ECharts；后端采用 Python、FastAPI、Pydantic 与 SQLAlchemy；数据库模型支持通过 DATABASE_URL 配置 MySQL，开发演示默认使用 SQLite，以降低部署门槛。Agent 执行模块首阶段采用规则化本地模拟器，避免将模拟结果误称为真实大模型结果；在导师确认模型、接口预算及数据处理要求后，再评估接入支持 Function Calling 的模型服务。")

    document.add_heading("3.5 可行性分析", level=2)
    add_paragraph(document, "技术可行性：课题主要工作由成熟的 Web 框架、关系型数据库、异步执行与图表组件构成，首阶段本地模拟工具无需外部 API 密钥；当前原型已形成执行引擎、指标计算、数据库模型、接口和前端页面的基础结构。")
    add_paragraph(document, "实验可行性：天气查询与单位换算等确定性任务易于定义预期工具、参数和结果；故障由测试环境按配置注入，可控制变量并重复运行。实验数据和报告会标注任务集规模、模拟器范围和策略配置，避免对真实模型泛化能力作过度推断。")
    add_paragraph(document, "进度与风险：任务书中进度日期尚未填写，具体起止时间需由导师确认。主要风险包括真实工具/API 的可用性和安全边界、模型调用成本与随机性、测试集规模偏小，以及指标口径不统一。拟优先完成离线闭环，之后按资源条件扩充任务和模型；接入外部工具时采用白名单与模拟接口，避免触及真实敏感数据或产生不可逆副作用。")

    document.add_heading("4. 项目特色与创新点", level=1)
    add_paragraph(document, "（1）过程级证据链：以单次工具调用为基本观测单元，保存工具、参数、结果、状态、耗时与重试轨迹，使失败定位不只依赖最终回答。")
    add_paragraph(document, "（2）受控故障与恢复对比：把工具异常作为独立实验变量，对同一任务和场景比较基线与自纠错策略，并保留完整配置以支持复跑。")
    add_paragraph(document, "（3）指标与诊断联动：指标统计、故障分类、原始调用记录和改进建议相互关联，使评测结果可回溯到具体调用证据。")
    add_paragraph(document, "（4）创新性表述边界：本课题的特色定位为面向本科毕业设计的工程化集成与可复现实验流程，不主张在通用 Agent 算法或故障诊断理论上取得首创性突破；实际贡献需以实现、测试数据及与既有基准的对比结果为依据。")

    document.add_heading("5. 进度安排", level=1)
    add_paragraph(document, "任务书中的起止日期和提交节点为空，以下仅据项目规划列出阶段任务，具体时间待导师确认；不得直接作为学院正式进度承诺。", first_line=False)
    schedule = document.add_table(rows=1, cols=3)
    schedule.style = "Table Grid"
    schedule.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, value in zip(schedule.rows[0].cells, ["阶段", "起止时间", "主要工作与阶段成果"]):
        set_cell_text(cell, value, True)
        set_cell_shading(cell, "EAF1EF")
    set_repeat_table_header(schedule.rows[0])
    stages = [
        ("一、需求与架构", "待确认", "核对任务书和学院模板；确定任务、故障模型、指标口径与系统边界。"),
        ("二、基础 Agent 与工具调用", "待确认", "完成模拟任务解析、工具选择、参数生成、调用和结果处理。"),
        ("三、工具模拟与故障注入", "待确认", "实现正常、超时、空结果、参数错误及执行失败等场景。"),
        ("四、轨迹记录与存储", "待确认", "完成执行轨迹、数据模型、历史查询和数据导出。"),
        ("五、自动评测与故障诊断", "待确认", "实现指标计算、故障分类和证据展示，补充核心测试。"),
        ("六、Web 可视化平台", "待确认", "完成任务配置、执行监控、结果图表和历史界面。"),
        ("七、对照实验与结果分析", "待确认", "固定实验配置，比较策略，整理数据、局限和结论。"),
        ("八、论文撰写与系统完善", "待确认", "完成论文初稿、修改、系统验收和材料归档。"),
    ]
    for stage in stages:
        cells = schedule.add_row().cells
        for cell, value in zip(cells, stage):
            set_cell_text(cell, value)
    for row in schedule.rows:
        for cell, width in zip(row.cells, [Cm(3.2), Cm(2.3), Cm(9.9)]):
            cell.width = width

    document.add_heading("6. 主要参考文献", level=1)
    add_paragraph(document, "说明：以下为与课题相关的代表性外文论文、公开预印本和国际标准候选清单。正式提交前请通过学校图书馆、出版社或标准数据库逐条核对作者、出版载体、卷期页码及版本，并按学院规定格式统一著录。", first_line=False)
    for index, reference in enumerate(REFERENCES, start=1):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(0.72)
        paragraph.paragraph_format.first_line_indent = Cm(-0.72)
        paragraph.paragraph_format.line_spacing = 1.15
        paragraph.paragraph_format.space_after = Pt(3)
        run = paragraph.add_run(f"[{index}] {reference}")
        run.font.size = Pt(9)
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    document.core_properties.title = "武汉大学本科毕业论文（设计）开题报告雏形"
    document.core_properties.subject = "面向工具调用的智能体自动化评测与故障诊断平台设计与实现"
    document.core_properties.author = "侯玉生"
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
