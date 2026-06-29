"""主程序：KG-RAG 医学题库测试系统

流程：SQLite 读取题目 → KG-RAG 接口 → 通用 LLM 接口 → 控制台输出

用法：
  python test_demo.py             随机测 1 道题
  python test_demo.py 5           指定题号
  python test_demo.py 1 2 3       指定多道题号
  python test_demo.py -n 5        随机抽 N 道题
  python test_demo.py --batch     遍历全部题目，保存结果到 results.json
"""
import sys
import time
import random
import json
import os
from datetime import datetime
from db_reader import read_one_question, read_all_questions, count_questions
from rag_api import query_rag
from llm_api import query_llm

# 结果输出目录
RESULT_DIR = os.path.dirname(os.path.abspath(__file__))


def format_question(q):
    """将一道题格式化为完整题干文本"""
    parts = [q["question"]]
    for label in ("A", "B", "C", "D", "E"):
        key = f"option_{label.lower()}"
        if q.get(key):
            parts.append(f"{label}. {q[key]}")
    return "\n".join(parts)


def print_result(q, full_question, rag_result, llm_result, t_rag, t_llm):
    """打印单题测试结果"""
    print()
    print("=" * 60)
    print(f"题号：{q['id']}")
    print(f"课程：{q.get('course', 'N/A')}")
    print(f"教材：{q.get('subject', 'N/A')}")
    print()
    print("题目：")
    print(full_question)
    print()
    print(f"标准答案：{q.get('answer', 'N/A')}")
    print()

    print("-" * 40)
    print("【KG-RAG】")
    print(f"答案：{rag_result['answer']}")
    print(f"(耗时 {t_rag:.1f}s, 状态: {'OK' if rag_result['ok'] else 'FAIL'})")
    print()

    print("-" * 40)
    print("【通用大模型】")
    print(f"答案：{llm_result['answer']}")
    print(f"(耗时 {t_llm:.1f}s, 状态: {'OK' if llm_result['ok'] else 'FAIL'})")
    print("=" * 60)


def test_one_question(q):
    """对一道题执行 KG-RAG + LLM 调用，返回结果 dict（不打印）"""
    full_question = format_question(q)

    # KG-RAG
    t0 = time.time()
    rag_result = query_rag(
        question=full_question,
        course_list=[q.get("course", "")] if q.get("course") else None,
        subject_list=[q.get("subject", "")] if q.get("subject") else None,
    )
    t_rag = time.time() - t0

    # 通用 LLM
    t0 = time.time()
    llm_result = query_llm(question=full_question)
    t_llm = time.time() - t0

    return {
        "id": q["id"],
        "course": q.get("course", ""),
        "subject": q.get("subject", ""),
        "question": full_question,
        "answer": q.get("answer", ""),
        "rag_answer": rag_result["answer"],
        "llm_answer": llm_result["answer"],
        "rag_time": round(t_rag, 2),
        "llm_time": round(t_llm, 2),
        "rag_ok": rag_result["ok"],
        "llm_ok": llm_result["ok"],
    }


def run_test(question_id=None):
    """执行一次测试（控制台输出）"""
    q = read_one_question(question_id)
    if q is None:
        print("[ERROR] 未读取到题目，请检查数据库")
        return None

    full_question = format_question(q)

    print(">>> 正在调用 KG-RAG ...", flush=True)
    t0 = time.time()
    rag_result = query_rag(
        question=full_question,
        course_list=[q.get("course", "")] if q.get("course") else None,
        subject_list=[q.get("subject", "")] if q.get("subject") else None,
    )
    t_rag = time.time() - t0

    print(">>> 正在调用通用大模型 ...", flush=True)
    t0 = time.time()
    llm_result = query_llm(question=full_question)
    t_llm = time.time() - t0

    print_result(q, full_question, rag_result, llm_result, t_rag, t_llm)

    return {
        "id": q["id"],
        "course": q.get("course", ""),
        "subject": q.get("subject", ""),
        "question": full_question,
        "answer": q.get("answer", ""),
        "rag_answer": rag_result["answer"],
        "llm_answer": llm_result["answer"],
        "rag_time": round(t_rag, 2),
        "llm_time": round(t_llm, 2),
        "rag_ok": rag_result["ok"],
        "llm_ok": llm_result["ok"],
    }


def run_batch(output_file="results.json"):
    """批量模式：遍历全部题目，逐题测试并保存结果"""
    all_qs = read_all_questions()
    total = len(all_qs)
    if total == 0:
        print("[ERROR] 题库为空")
        return

    output_path = os.path.join(RESULT_DIR, output_file)
    results = []
    rag_fail = 0
    llm_fail = 0
    t_start = time.time()

    print(f"[INFO] 批量测试开始，共 {total} 道题")
    print(f"[INFO] 结果将保存到：{output_path}")
    print()

    for i, q in enumerate(all_qs, start=1):
        qid = q["id"]
        course = q.get("course", "?")
        print(f"[{i}/{total}] Q#{qid} {course} ... ", end="", flush=True)

        t0 = time.time()
        result = test_one_question(q)
        elapsed = time.time() - t0

        if not result["rag_ok"]:
            rag_fail += 1
        if not result["llm_ok"]:
            llm_fail += 1

        results.append(result)

        status_parts = []
        status_parts.append("RAG=OK" if result["rag_ok"] else "RAG=FAIL")
        status_parts.append("LLM=OK" if result["llm_ok"] else "LLM=FAIL")
        print(f"完成 ({', '.join(status_parts)}, 耗时 {elapsed:.1f}s)", flush=True)

    t_total = time.time() - t_start

    # 保存 JSON
    output = {
        "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_questions": total,
        "rag_fail_count": rag_fail,
        "llm_fail_count": llm_fail,
        "total_time_s": round(t_total, 1),
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 汇总输出
    print()
    print("=" * 60)
    print("  批量测试完成")
    print("=" * 60)
    print(f"  总题数：{total}")
    print(f"  总耗时：{t_total:.1f}s ({t_total/60:.1f}min)")
    print(f"  KG-RAG 失败：{rag_fail} 次")
    print(f"  通用 LLM 失败：{llm_fail} 次")
    print(f"  结果已保存：{output_path}")
    print("=" * 60)


if __name__ == "__main__":
    total = count_questions()
    print("[INFO] 题库共 " + str(total) + " 道题")
    print()
    args = sys.argv[1:]

    if not args:
        # 默认：随机 1 道
        run_test()
    elif args[0] == "--batch":
        # 批量模式：遍历全部题目
        output_file = args[1] if len(args) >= 2 else "results.json"
        run_batch(output_file)
    elif args[0] == "-n" and len(args) >= 2:
        # -n N：随机 N 道
        count = min(int(args[1]), total)
        print("[INFO] 随机抽取 " + str(count) + " 道题")
        print()
        all_qs = read_all_questions()
        for q in random.sample(all_qs, count):
            run_test(q["id"])
    else:
        # 指定题号（一个或多个）
        for arg in args:
            run_test(int(arg))
