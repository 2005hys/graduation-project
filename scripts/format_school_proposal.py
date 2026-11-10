from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "开题报告雏形.docx"
OUTPUT = ROOT / "docs" / "开题报告-学校表格版.docx"
HEADINGS = {
    "1. 选题目的和意义",
    "2. 国内外研究现状和发展趋势",
    "3. 研究内容、研究方法、技术路线及可行性分析",
    "4. 项目特色与创新点",
    "5. 进度安排",
    "6. 主要参考文献",
}


def add_page_field(paragraph) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, end])


def copy_table(source_table, document: Document) -> None:
    column_count = len(source_table.columns)
    target = document.add_table(rows=0, cols=column_count)
    target.style = "Table Grid"
    target.autofit = True
    for row_index, source_row in enumerate(source_table.rows):
        cells = target.add_row().cells
        for index, source_cell in enumerate(source_row.cells):
            cell = cells[index]
            cell.text = source_cell.text
            cell.vertical_alignment = 1
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.first_line_indent = Cm(0)
                paragraph.paragraph_format.line_spacing = 1.0
                paragraph.paragraph_format.space_after = Pt(1)
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if row_index == 0 else WD_ALIGN_PARAGRAPH.LEFT
                for run in paragraph.runs:
                    run.font.name = "宋体"
                    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
                    run.font.size = Pt(8.5)
                    if row_index == 0:
                        run.bold = True
            if row_index == 0:
                shading = OxmlElement("w:shd")
                shading.set(qn("w:fill"), "EAF1EF")
                cell._tc.get_or_add_tcPr().append(shading)


def copy_body(source: Document, document: Document) -> None:
    body_started = False
    for element in source.element.body.iterchildren():
        if element.tag == qn("w:p"):
            paragraph = Paragraph(element, source)
            text = paragraph.text.strip()
            if text in HEADINGS:
                body_started = True
                document.add_heading(text, level=1)
            elif body_started and text:
                target = document.add_paragraph()
                target.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                target.paragraph_format.widow_control = True
                target.paragraph_format.line_spacing = 1.18
                if re.match(r"^\[\d+\]", text):
                    target.paragraph_format.left_indent = Cm(0.65)
                    target.paragraph_format.first_line_indent = Cm(-0.65)
                    run = target.add_run(text)
                    run.font.size = Pt(8.5)
                    run.font.name = "Times New Roman"
                    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
                else:
                    target.paragraph_format.first_line_indent = Cm(0.7)
                    target.add_run(text)
        elif element.tag == qn("w:tbl") and body_started:
            copy_table(Table(element, source), document)
            document.add_paragraph().paragraph_format.space_after = Pt(2)


def build() -> Path:
    source = Document(SOURCE)
    document = Document()
    section = document.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.35)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.45)
    section.right_margin = Cm(2.35)

    normal = document.styles["Normal"]
    normal.font.name = "宋体"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(35, 43, 47)
    normal.paragraph_format.line_spacing = 1.3
    normal.paragraph_format.space_after = Pt(3)
    for name, size in [("Heading 1", 13), ("Heading 2", 11)]:
        style = document.styles[name]
        style.font.name = "黑体"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(25, 58, 67)
        style.paragraph_format.space_before = Pt(8)
        style.paragraph_format.space_after = Pt(3)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_run = header.add_run("武汉大学本科毕业论文（设计）开题报告")
    header_run.font.size = Pt(8)
    header_run.font.color.rgb = RGBColor(120, 132, 133)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_field(footer)

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("武汉大学本科毕业论文（设计）开题报告")
    title_run.bold = True
    title_run.font.name = "黑体"
    title_run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    title_run.font.size = Pt(17)
    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle.add_run("学校表格内容版 · 雏形稿")
    subtitle_run.font.size = Pt(9)
    subtitle_run.font.color.rgb = RGBColor(120, 132, 133)

    info = document.add_table(rows=3, cols=4)
    info.style = "Table Grid"
    info.autofit = True
    values = [
        ["学生姓名", "侯玉生", "学号", "2023302111225"],
        ["学院", "计算机学院", "专业", "软件工程"],
        ["指导教师", "刘进（教授）", "题目类别", "待确认"],
    ]
    for row_index, row_values in enumerate(values):
        for column_index, value in enumerate(row_values):
            cell = info.cell(row_index, column_index)
            cell.text = value
            cell.vertical_alignment = 1
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.paragraph_format.first_line_indent = Cm(0)
                for run in paragraph.runs:
                    run.font.name = "宋体"
                    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
                    run.font.size = Pt(9)
            if column_index in (0, 2):
                shading = OxmlElement("w:shd")
                shading.set(qn("w:fill"), "EAF1EF")
                cell._tc.get_or_add_tcPr().append(shading)

    project_title = document.add_paragraph()
    project_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    project_title.paragraph_format.space_before = Pt(8)
    project_title.paragraph_format.space_after = Pt(11)
    project_title_run = project_title.add_run("面向工具调用的智能体自动化评测与故障诊断平台设计与实现")
    project_title_run.bold = True
    project_title_run.font.name = "黑体"
    project_title_run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    project_title_run.font.size = Pt(13)

    copy_body(source, document)
    document.core_properties.title = "开题报告雏形（学校表格内容版）"
    document.core_properties.subject = "面向工具调用的智能体自动化评测与故障诊断平台设计与实现"
    document.core_properties.author = "侯玉生"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build())
