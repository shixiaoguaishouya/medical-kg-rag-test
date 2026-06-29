"""
配置文件
"""

import os as _os
DB_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "medical_qa.db")

RAG_HOST = "localhost"
RAG_PORT = 4103
RAG_PATH = "/query_with_triples"
RAG_KB_ID = "69115c8e7e67a85a7b8c2cfb"
RAG_ALGORITHM_ID = "68d4f55224c9a461c422d4e4"
RAG_LLM_ID = "6a379d41b37ed8b55c7cb758"
RAG_SCENE = "basic_med_fm_single_choice"

LLM_URL = "http://api.vgpu.scu.edu.cn/v1/chat/completions"
LLM_API_KEY = "sk-ce554825fffb473b9a88114e780724f2"
LLM_MODEL = "Qwen35"

SYSTEM_PROMPT = (
    "你是一名基础医学领域专家。\n\n"
    "请结合知识库检索到的教材内容回答下面的单项选择题。\n\n"
    "要求：\n"
    "1. 优先依据检索结果回答；\n"
    "2. 给出最终正确选项（A/B/C/D/E）；\n"
    "3. 简要说明判断依据；\n"
    "4. 若检索信息不足，可结合医学专业知识进行合理判断，但不要编造教材内容。"
)
