"""判题模块：从模型回答中提取选项字母，判断是否正确"""

import re


def extract_option(text):
    """从模型回答文本中提取最终选项字母（A/B/C/D/E）

    匹配策略（按优先级）：
    1. 显式标记："正确选项"、"答案"、"选" 后紧跟的字母
    2. 行首独立出现的选项字母
    3. 全文最后出现的独立大写字母 A-E
    4. 回退：全文搜索 A/B/C/D/E

    返回：大写字母如 "A"，或 None
    """
    if not text:
        return None

    text_clean = text.strip()

    # 策略1：匹配显式标记
    patterns = [
        r"(?:正确选项|正确答案|答案|选项)\s*(?:是|为|：|:|[.。])\s*([A-Ea-e])",
        r"(?:选择|选)\s*([A-Ea-e])",
        r"(?:故选|因此选|所以选|应该选)\s*([A-Ea-e])",
        r"([A-Ea-e])\s*(?:正确|是正确答案|是答案)",
        r"(?:最终答案|我的答案)\s*(?:是|为|：|:|[.。])\s*([A-Ea-e])",
    ]
    for pat in patterns:
        m = re.search(pat, text_clean)
        if m:
            return m.group(1).upper()

    # 策略2：行首独立出现的选项（如 "B。xxx" 或 "B. xxx"）
    m = re.search(r"^([A-Ea-e])\s*[.。、)]", text_clean, re.MULTILINE)
    if m:
        return m.group(1).upper()

    # 策略3：全文最后一个独立出现的 A-E
    matches = re.findall(r"[A-Ea-e]", text_clean)
    if matches:
        return matches[-1].upper()

    return None


def is_correct(model_answer, standard_answer):
    """判断模型回答是否正确

    model_answer: str — 模型返回的完整回答文本
    standard_answer: str — 标准答案，如 "A"、"B"

    返回：(bool, str) — (是否正确, 提取到的选项)
    """
    extracted = extract_option(model_answer)
    std = standard_answer.strip().upper() if standard_answer else ""

    if extracted is None:
        return False, "?"
    return extracted == std, extracted


def count_correct(results):
    """对一批结果统计正确数量

    results: list[dict] — 每项包含 rag_answer, llm_answer, answer

    返回 dict 包含 rag/llm 的正确数和总数
    """
    rag_correct = 0
    llm_correct = 0
    total = len(results)

    for r in results:
        rag_ok, _ = is_correct(r.get("rag_answer", ""), r.get("answer", ""))
        llm_ok, _ = is_correct(r.get("llm_answer", ""), r.get("answer", ""))
        if rag_ok:
            rag_correct += 1
        if llm_ok:
            llm_correct += 1

    return {
        "total": total,
        "rag_correct": rag_correct,
        "llm_correct": llm_correct,
        "rag_accuracy": round(rag_correct / total, 4) if total > 0 else 0,
        "llm_accuracy": round(llm_correct / total, 4) if total > 0 else 0,
    }


def stats_by_course(results):
    """按课程分组统计正确率

    返回 list[dict]：每个课程一行
    """
    from collections import defaultdict
    groups = defaultdict(list)
    for r in results:
        groups[r.get("course", "未知")].append(r)

    stats = []
    for course in sorted(groups.keys()):
        items = groups[course]
        total = len(items)
        rag_correct = sum(
            1 for r in items
            if is_correct(r.get("rag_answer", ""), r.get("answer", ""))[0]
        )
        llm_correct = sum(
            1 for r in items
            if is_correct(r.get("llm_answer", ""), r.get("answer", ""))[0]
        )
        stats.append({
            "course": course,
            "total": total,
            "rag_correct": rag_correct,
            "llm_correct": llm_correct,
            "rag_accuracy": round(rag_correct / total, 4) if total > 0 else 0,
            "llm_accuracy": round(llm_correct / total, 4) if total > 0 else 0,
        })

    return stats
