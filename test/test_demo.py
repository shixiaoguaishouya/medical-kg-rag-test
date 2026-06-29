"""主程序：KG-RAG 医学题库测试系统

流程：SQLite 读取题目 -> KG-RAG 接口 -> 通用 LLM 接口 -> 判题 -> 输出

用法：
  python test_demo.py                  随机测 1 道题
  python test_demo.py 5                指定题号
  python test_demo.py 1 2 3            指定多道题号
  python test_demo.py -n 5             随机抽 N 道题
  python test_demo.py --batch          遍历全部题目，保存 results.json
  python test_demo.py --batch --export  遍历全部题目 + 导出 Excel
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
from judge import is_correct, count_correct, stats_by_course, stats_by_difficulty

RESULT_DIR = os.path.dirname(os.path.abspath(__file__))


def format_question(q):
    """question 字段已包含题干 + 选项，直接返回"""
    return q["question"]


def test_one_question(q):
    """对一道题执行 KG-RAG + LLM 调用，返回结果 dict（不打印）"""
    full_question = format_question(q)

    # KG-RAG
    t0 = time.time()
    rag_result = query_rag(
        question=full_question,
        course_list=[q.get("course", "")] if q.get("course") else None,
        subject_list=[],
    )
    t_rag = time.time() - t0

    # 通用 LLM
    t0 = time.time()
    llm_result = query_llm(question=full_question)
    t_llm = time.time() - t0

    # 判题
    rag_correct, rag_opt = is_correct(rag_result["answer"], q.get("answer", ""))
    llm_correct, llm_opt = is_correct(llm_result["answer"], q.get("answer", ""))

    return {
        "id": q["id"],
        "course": q.get("course", ""),
        "subtype": q.get("subtype", ""),
        "difficulty": q.get("difficulty", ""),
        "question": full_question,
        "answer": q.get("answer", ""),
        "rag_answer": rag_result["answer"],
        "llm_answer": llm_result["answer"],
        "rag_opt": rag_opt,
        "llm_opt": llm_opt,
        "rag_correct": rag_correct,
        "llm_correct": llm_correct,
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

    print(">>> 调用 KG-RAG ...", flush=True)
    t0 = time.time()
    rag_result = query_rag(
        question=full_question,
        course_list=[q.get("course", "")] if q.get("course") else None,
        subject_list=[],
    )
    t_rag = time.time() - t0

    print(">>> 调用通用大模型 ...", flush=True)
    t0 = time.time()
    llm_result = query_llm(question=full_question)
    t_llm = time.time() - t0

    # 判题
    rag_correct, rag_opt = is_correct(rag_result["answer"], q.get("answer", ""))
    llm_correct, llm_opt = is_correct(llm_result["answer"], q.get("answer", ""))

    # 输出
    print()
    print("=" * 60)
    print(f"题号：{q['id']}")
    print(f"课程：{q.get('course', 'N/A')}")
    print(f"分类：{q.get('subtype', 'N/A')}")
    print(f"难度：{q.get('difficulty', 'N/A')}")
    print()
    print("题目：")
    print(full_question)
    print()
    print(f"标准答案：{q.get('answer', 'N/A')}")
    print()

    print("-" * 40)
    print(f"【KG-RAG】-> 提取选项: {rag_opt} | {'正确' if rag_correct else '错误'}")
    print(f"回答：{rag_result['answer']}")
    print(f"(耗时 {t_rag:.1f}s, 状态: {'OK' if rag_result['ok'] else 'FAIL'})")
    print()

    print("-" * 40)
    print(f"【通用大模型】-> 提取选项: {llm_opt} | {'正确' if llm_correct else '错误'}")
    print(f"回答：{llm_result['answer']}")
    print(f"(耗时 {t_llm:.1f}s, 状态: {'OK' if llm_result['ok'] else 'FAIL'})")
    print("=" * 60)

    return {
        "id": q["id"],
        "course": q.get("course", ""),
        "subtype": q.get("subtype", ""),
        "difficulty": q.get("difficulty", ""),
        "question": full_question,
        "answer": q.get("answer", ""),
        "rag_answer": rag_result["answer"],
        "llm_answer": llm_result["answer"],
        "rag_opt": rag_opt,
        "llm_opt": llm_opt,
        "rag_correct": rag_correct,
        "llm_correct": llm_correct,
        "rag_time": round(t_rag, 2),
        "llm_time": round(t_llm, 2),
        "rag_ok": rag_result["ok"],
        "llm_ok": llm_result["ok"],
    }


def run_batch(output_file="results.json", export_excel=False):
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
    print(f"[INFO] 结果保存到：{output_path}")
    if export_excel:
        excel_path = output_path.replace(".json", ".xlsx")
        print(f"[INFO] Excel 保存到：{excel_path}")
    print()

    for i, q in enumerate(all_qs, start=1):
        qid = q["id"]
        course = q.get("course", "?")
        diff = q.get("difficulty", "")
        print(f"[{i}/{total}] Q#{qid} {course}({diff}) ... ", end="", flush=True)

        t0 = time.time()
        result = test_one_question(q)
        elapsed = time.time() - t0

        if not result["rag_ok"]:
            rag_fail += 1
        if not result["llm_ok"]:
            llm_fail += 1

        results.append(result)

        rag_mark = "v" if result["rag_correct"] else "x"
        llm_mark = "v" if result["llm_correct"] else "x"
        rag_st = "OK" if result["rag_ok"] else "FAIL"
        llm_st = "OK" if result["llm_ok"] else "FAIL"
        print(f"完成 (RAG={rag_st}{rag_mark}, LLM={llm_st}{llm_mark}, {elapsed:.1f}s)", flush=True)

    t_total = time.time() - t_start

    # 统计
    overall = count_correct(results)
    by_course = stats_by_course(results)
    by_diff = stats_by_difficulty(results)

    # JSON
    output = {
        "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_questions": total,
        "rag_fail_count": rag_fail,
        "llm_fail_count": llm_fail,
        "total_time_s": round(t_total, 1),
        "overall": overall,
        "by_course": by_course,
        "by_difficulty": by_diff,
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 汇总
    print()
    print("=" * 60)
    print("  批量测试完成")
    print("=" * 60)
    print(f"  总题数：{total}")
    print(f"  总耗时：{t_total:.1f}s ({t_total/60:.1f}min)")
    print(f"  KG-RAG 失败：{rag_fail} 次")
    print(f"  通用 LLM 失败：{llm_fail} 次")
    print()
    print(f"  KG-RAG 正确率：{overall['rag_correct']}/{overall['total']} = {overall['rag_accuracy']:.2%}")
    print(f"  通用LLM 正确率：{overall['llm_correct']}/{overall['total']} = {overall['llm_accuracy']:.2%}")
    print(f"  结果已保存：{output_path}")
    print("=" * 60)

    # 按课程
    if len(by_course) > 1:
        print()
        print("--- 按课程正确率 ---")
        for cs in by_course:
            print(f"  {cs['course']}: RAG={cs['rag_accuracy']:.2%}  LLM={cs['llm_accuracy']:.2%}  (共{cs['total']}题)")

    # 按难度
    if by_diff:
        print()
        print("--- 按难度正确率 ---")
        for ds in by_diff:
            print(f"  {ds['difficulty']}: RAG={ds['rag_accuracy']:.2%}  LLM={ds['llm_accuracy']:.2%}  (共{ds['total']}题)")

    # Excel
    if export_excel:
        print()
        print(">>> 生成 Excel ...", flush=True)
        from exporter import export_results
        stats = {
            "test_time": output["test_time"],
            "rag_fail_count": rag_fail,
            "llm_fail_count": llm_fail,
            "total_time_s": round(t_total, 1),
            "overall": overall,
            "by_course": by_course,
            "by_difficulty": by_diff,
        }
        export_results(results, stats, excel_path)
        print(f"[INFO] Excel 已保存：{excel_path}")


if __name__ == "__main__":
    total = count_questions()
    print(f"[INFO] 题库共 {total} 道题")
    print()
    args = sys.argv[1:]

    export_excel = "--export" in args
    batch_mode = "--batch" in args
    clean_args = [a for a in args if a not in ("--export",)]

    if not clean_args:
        run_test()
    elif batch_mode:
        output_file = clean_args[1] if len(clean_args) >= 2 and not clean_args[1].startswith("-") else "results.json"
        run_batch(output_file, export_excel=export_excel)
    elif clean_args[0] == "-n" and len(clean_args) >= 2:
        count = min(int(clean_args[1]), total)
        print(f"[INFO] 随机抽取 {count} 道题")
        print()
        all_qs = read_all_questions()
        for q in random.sample(all_qs, count):
            run_test(q["id"])
    else:
        for arg in clean_args:
            run_test(int(arg))
