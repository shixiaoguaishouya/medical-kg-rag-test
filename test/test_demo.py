"""
主程序：KG-RAG 医学题库测试系统 MVP

流程：SQLite 读取题目 → KG-RAG 接口 → 通用 LLM 接口 → 控制台输出
"""
import sys
import time
from db_reader import read_one_question, count_questions
from rag_api import query_rag
from llm_api import query_llm


def format_question(q):
    """将一道题格式化为完整题干文本"""
    parts = [q["question"]]
    for label in ("A", "B", "C", "D", "E"):
        key = f"option_{label.lower()}"
        if q.get(key):
            parts.append(f"{label}. {q[key]}")
    return "\n".join(parts)


def run_test(question_id=None):
    """执行一次测试"""
    # ---------- 1. 读取题目 ----------
    q = read_one_question(question_id)
    if q is None:
        print("[ERROR] 未读取到题目，请检查数据库")
        return

    full_question = format_question(q)

    # ---------- 2. 调用 KG-RAG ----------
    print(">>> 正在调用 KG-RAG ...", flush=True)
    t0 = time.time()
    rag_result = query_rag(
        question=full_question,
        course_list=[q.get("course", "")] if q.get("course") else None,
        subject_list=[q.get("subject", "")] if q.get("subject") else None,
    )
    t_rag = time.time() - t0

    # ---------- 3. 调用通用 LLM ----------
    print(">>> 正在调用通用大模型 ...", flush=True)
    t0 = time.time()
    llm_result = query_llm(question=full_question)
    t_llm = time.time() - t0

    # ---------- 4. 输出结果 ----------
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


if __name__ == "__main__":
    total = count_questions()
    print("[INFO] 题库共 " + str(total) + " 道题")
    print()
    args = sys.argv[1:]

    if not args:
        # 默认：随机 1 道
        run_test()
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