"""
封装 OpenAI Compatible API（通用大模型）
"""
import requests
from config import LLM_URL, LLM_API_KEY, LLM_MODEL


def query_llm(question, model=None):
    """
    调用通用大模型

    参数：
        question : str   题目文本
        model    : str | None  模型名，默认使用配置中的 LLM_MODEL

    返回：
        dict {
            "answer" : str,
            "raw"    : dict,
            "ok"     : bool,
        }
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }

    data = {
        "model": model or LLM_MODEL,
        "messages": [{"role": "user", "content": question}],
        "stream": False,
    }

    try:
        resp = requests.post(LLM_URL, headers=headers, json=data, timeout=120)
        resp.raise_for_status()
        raw = resp.json()

        # 提取 answer 字段
        answer = (
            raw.get("choices", [{}])[0].get("message", {}).get("content", "")
            or raw.get("answer")
            or str(raw)
        )
        return {"answer": answer, "raw": raw, "ok": True}
    except Exception as e:
        return {"answer": f"[ERROR] {e}", "raw": None, "ok": False}
