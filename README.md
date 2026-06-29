# 医学题库 KG-RAG 测试系统

对比 **KG-RAG（知识库增强问答）** 与 **通用大模型（Qwen35）** 在医学选择题上的回答效果。

## 项目结构

```
test/
├── config.py          # 配置文件（API地址、Key、DB路径等）
├── db_reader.py       # SQLite 题库读取
├── rag_api.py         # KG-RAG 知识库接口
├── llm_api.py         # 通用大模型接口（OpenAI Compatible）
└── test_demo.py       # 主程序
```

## 流程

```
SQLite 题库 → 读取题目 → KG-RAG 接口  → 控制台输出 / JSON 保存
                     → 通用 LLM 接口 →
```

## 环境要求

- Python 3.8+
- 依赖包：`requests`
- 服务器上需运行 KG-RAG 服务（localhost:4103）
- 通用大模型接口需网络可达

```bash
pip install requests
```

## 配置

编辑 `test/config.py`：

```python
# SQLite 题库路径（Linux）
DB_PATH = "/tmp/medical_qa.db"

# KG-RAG 接口
RAG_HOST = "localhost"
RAG_PORT = 4103

# 通用大模型
LLM_URL = "http://api.vgpu.scu.edu.cn/v1/chat/completions"
LLM_API_KEY = "sk-ce554825fffb473b9a88114e780724f2"
LLM_MODEL = "Qwen35"
```

## 用法

```bash
cd test

# 随机测 1 道题
python test_demo.py

# 指定题号
python test_demo.py 5

# 指定多道题号
python test_demo.py 1 2 3

# 随机抽 N 道题
python test_demo.py -n 5

# 批量测试全部题目，结果保存到 results.json
python test_demo.py --batch

# 批量测试，指定输出文件
python test_demo.py --batch my_results.json
```

## 批量测试

`--batch` 模式会遍历题库中所有题目，每道题分别调用 KG-RAG 和通用大模型，将结果保存为 JSON 文件。

### 进度显示

```
[INFO] 批量测试开始，共 500 道题
[INFO] 结果将保存到：.../test/results.json

[1/500] Q#1 医学微生物学 ... 完成 (RAG=OK, LLM=OK, 耗时 4.2s)
[2/500] Q#2 生理学 ... 完成 (RAG=OK, LLM=OK, 耗时 3.8s)
...
```

### 测试汇总

```
============================================================
  批量测试完成
============================================================
  总题数：500
  总耗时：2100.5s (35.0min)
  KG-RAG 失败：3 次
  通用 LLM 失败：0 次
  结果已保存：.../test/results.json
============================================================
```

### results.json 结构

```json
{
  "test_time": "2026-06-29 15:30:00",
  "total_questions": 500,
  "rag_fail_count": 3,
  "llm_fail_count": 0,
  "total_time_s": 2100.5,
  "results": [
    {
      "id": 1,
      "course": "医学微生物学",
      "subject": "医学微生物学(第9版)",
      "question": "质粒是：\nA. 染色体外的遗传物质\nB. ...",
      "answer": "A",
      "rag_answer": "A。质粒是细菌染色体外的...",
      "llm_answer": "A。质粒存在于细胞质中...",
      "rag_ok": true,
      "llm_ok": true,
      "rag_time": 4.2,
      "llm_time": 4.2
    }
  ]
}
```

### 容错机制

单道题的 API 调用失败不会中断整个批量测试。失败题目会在进度行标记 `RAG=FAIL` 或 `LLM=FAIL`，并继续测试下一题。最终汇总会统计总失败次数。

## 输出示例（单题模式）

```
[INFO] 题库共 5000 道题

>>> 正在调用 KG-RAG ...
>>> 正在调用通用大模型 ...

============================================================
题号：42
课程：生理学
教材：生理学(第9版)

题目：
内环境稳态是指：
A. 细胞内液的化学成分相对恒定
B. 细胞外液的化学成分相对恒定
C. 体液的化学成分相对恒定
D. 血浆的化学成分相对恒定
E. 组织液的化学成分相对恒定

标准答案：B

----------------------------------------
【KG-RAG】
答案：B。根据教材内容，内环境即细胞外液...
(耗时 3.2s, 状态: OK)

----------------------------------------
【通用大模型】
答案：B。细胞外液是机体内细胞直接生活的环境...
(耗时 1.8s, 状态: OK)
============================================================
```

## 部署到 Linux 服务器

上传 `test/` 目录下 5 个文件即可：

```
test/
├── config.py
├── db_reader.py
├── rag_api.py
├── llm_api.py
└── test_demo.py
```

确保 `config.py` 中 `DB_PATH` 指向服务器上的题库路径（默认 `/tmp/medical_qa.db`）。

## 版本计划

| 版本 | 功能 | 状态 |
|------|------|------|
| v1 | 单题/少量题测试，控制台输出 | ✅ 完成 |
| v2 | 遍历题库批量测试，JSON 保存，容错与进度显示 | ✅ 当前 |
| v3 | 自动判对错、统计 Accuracy、导出 Excel | 📋 计划中 |
| v4 | 按课程统计、多模型对比、Prompt 对比、图表输出 | 📋 计划中 |
