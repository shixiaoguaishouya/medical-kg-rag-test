"""Excel 导出模块：生成测试结果 Excel 文件"""

import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter


# 样式定义
HEADER_FONT = Font(bold=True, size=11)
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FONT_WHITE = Font(bold=True, size=11, color="FFFFFF")
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)
CENTER = Alignment(horizontal="center", vertical="center")
WRAP = Alignment(horizontal="left", vertical="top", wrap_text=True)


def _style_header(ws, row, col_count):
    """给表头行加样式"""
    for col in range(1, col_count + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = HEADER_FONT_WHITE
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = THIN_BORDER


def _auto_width(ws, min_width=8, max_width=50):
    """自动调整列宽"""
    for col_cells in ws.columns:
        col_letter = get_column_letter(col_cells[0].column)
        max_len = 0
        for cell in col_cells:
            if cell.value:
                # 中文字符算2个宽度
                val = str(cell.value)
                length = sum(2 if ord(c) > 127 else 1 for c in val[:100])
                max_len = max(max_len, length)
        ws.column_dimensions[col_letter].width = max(min_width, min(max_len + 2, max_width))


def export_results(results, stats, output_path):
    """导出测试结果到 Excel

    results: list[dict] — 逐题测试结果（含 rag_correct, llm_correct 等）
    stats: dict — 总体统计（from judge.count_correct）
    output_path: str — 输出文件路径
    """
    wb = Workbook()

    # ========== Sheet 1: 逐题明细 ==========
    ws1 = wb.active
    ws1.title = "逐题明细"

    headers1 = [
        "题号", "课程", "教材",
        "题目", "标准答案",
        "KG-RAG回答", "RAG提取选项", "RAG结果",
        "通用LLM回答", "LLM提取选项", "LLM结果",
    ]
    for col, h in enumerate(headers1, 1):
        ws1.cell(row=1, column=col, value=h)
    _style_header(ws1, 1, len(headers1))

    from judge import is_correct

    for i, r in enumerate(results, start=2):
        rag_correct, rag_opt = is_correct(r.get("rag_answer", ""), r.get("answer", ""))
        llm_correct, llm_opt = is_correct(r.get("llm_answer", ""), r.get("answer", ""))

        row_data = [
            r.get("id", ""),
            r.get("course", ""),
            r.get("subject", ""),
            r.get("question", ""),
            r.get("answer", ""),
            r.get("rag_answer", ""),
            rag_opt,
            "✓ 正确" if rag_correct else "✗ 错误",
            r.get("llm_answer", ""),
            llm_opt,
            "✓ 正确" if llm_correct else "✗ 错误",
        ]
        for col, val in enumerate(row_data, 1):
            cell = ws1.cell(row=i, column=col, value=val)
            cell.border = THIN_BORDER
            if col in (4, 6, 9):
                cell.alignment = WRAP
            else:
                cell.alignment = CENTER

            # 正确/错误着色
            if col in (8, 11):
                if "正确" in str(val):
                    cell.font = Font(color="008000")
                else:
                    cell.font = Font(color="CC0000")

    _auto_width(ws1)
    # 题目和回答列设宽一些
    ws1.column_dimensions["D"].width = 45
    ws1.column_dimensions["F"].width = 50
    ws1.column_dimensions["I"].width = 50

    # ========== Sheet 2: 按课程汇总 ==========
    ws2 = wb.create_sheet("按课程汇总")

    headers2 = [
        "课程", "题目数",
        "KG-RAG正确数", "KG-RAG正确率",
        "通用LLM正确数", "通用LLM正确率",
    ]
    for col, h in enumerate(headers2, 1):
        ws2.cell(row=1, column=col, value=h)
    _style_header(ws2, 1, len(headers2))

    course_stats = stats.get("by_course", [])
    for i, cs in enumerate(course_stats, start=2):
        row_data = [
            cs["course"],
            cs["total"],
            cs["rag_correct"],
            cs["rag_accuracy"],
            cs["llm_correct"],
            cs["llm_accuracy"],
        ]
        for col, val in enumerate(row_data, 1):
            cell = ws2.cell(row=i, column=col, value=val)
            cell.border = THIN_BORDER
            cell.alignment = CENTER
            if col in (4, 6):
                cell.number_format = "0.00%"

    # 合计行
    total_row = len(course_stats) + 2
    overall = stats.get("overall", {})
    summary_data = [
        "合计",
        overall.get("total", 0),
        overall.get("rag_correct", 0),
        overall.get("rag_accuracy", 0),
        overall.get("llm_correct", 0),
        overall.get("llm_accuracy", 0),
    ]
    for col, val in enumerate(summary_data, 1):
        cell = ws2.cell(row=total_row, column=col, value=val)
        cell.border = THIN_BORDER
        cell.alignment = CENTER
        cell.font = Font(bold=True)
        if col in (4, 6):
            cell.number_format = "0.00%"

    _auto_width(ws2)

    # ========== Sheet 3: 总体统计 ==========
    ws3 = wb.create_sheet("总体统计")

    info_data = [
        ("测试时间", stats.get("test_time", "")),
        ("总题数", overall.get("total", 0)),
        ("", ""),
        ("KG-RAG 正确数", overall.get("rag_correct", 0)),
        ("KG-RAG 正确率", overall.get("rag_accuracy", 0)),
        ("KG-RAG 接口失败", stats.get("rag_fail_count", 0)),
        ("", ""),
        ("通用LLM 正确数", overall.get("llm_correct", 0)),
        ("通用LLM 正确率", overall.get("llm_accuracy", 0)),
        ("通用LLM 接口失败", stats.get("llm_fail_count", 0)),
        ("", ""),
        ("总耗时(秒)", stats.get("total_time_s", 0)),
    ]

    headers3 = ["指标", "数值"]
    for col, h in enumerate(headers3, 1):
        cell = ws3.cell(row=1, column=col, value=h)
        cell.font = HEADER_FONT_WHITE
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = THIN_BORDER

    for i, (label, val) in enumerate(info_data, start=2):
        ws3.cell(row=i, column=1, value=label).border = THIN_BORDER
        cell = ws3.cell(row=i, column=2, value=val)
        cell.border = THIN_BORDER
        cell.alignment = CENTER
        if isinstance(val, float) and 0 < val < 1:
            cell.number_format = "0.00%"

    _auto_width(ws3)

    wb.save(output_path)
    return output_path
