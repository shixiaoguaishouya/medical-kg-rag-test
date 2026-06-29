"""
封装 KG-RAG 知识库接口
"""
import http.client
import json
from config import (
    RAG_HOST, RAG_PORT, RAG_PATH,
    RAG_KB_ID, RAG_ALGORITHM_ID, RAG_LLM_ID, RAG_SCENE,
    SYSTEM_PROMPT,
)


def query_rag(question, course_list=None, subject_list=None):
    """
    调用 KG-RAG 知识库接口

    参数：
        question     : str   题目文本
        course_list  : list[str] | None  课程列表
        subject_list : list[str] | None  教材列表

    返回：
        dict {
            "answer" : str,
            "raw"    : dict,   # 原始返回
            "ok"     : bool,
        }
    """
    payload = {
        "question": question,
        "kb_id": RAG_KB_ID,
        "rag_algorithm_id": RAG_ALGORITHM_ID,
        "llm_id": RAG_LLM_ID,
        "course_list": course_list or [],
        "subject_list": subject_list or [],
        "scene": RAG_SCENE,
        "stream": False,
        "system_prompt": SYSTEM_PROMPT,
    }

    headers = {
        "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Host": f"{RAG_HOST}:{RAG_PORT}",
        "Connection": "keep-alive",
    }

    try:
        conn = http.client.HTTPConnection(RAG_HOST, RAG_PORT, timeout=120)
        conn.request("POST", RAG_PATH, json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        conn.close()

        raw = json.loads(data)
        # 尝试从常见字段提取回答
        answer = (
            raw.get("answer")
            or raw.get("data", {}).get("answer")
            or raw.get("response")
            or raw.get("result", {}).get("answer")
            or data
        )
        return {"answer": answer, "raw": raw, "ok": True}
    except Exception as e:
        return {"answer": f"[ERROR] {e}", "raw": None, "ok": False}
