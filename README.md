# 医学题库 KG-RAG 测试系统

对比 **KG-RAG（知识库增强问答）** 与 **通用大模型（Qwen35）** 在医学选择题上的回答效果。

## 项目结构

```
test/
├── config.py          # 配置文件（API地址、Key、DB路径等）
├── db_reader.py       # SQLite 题库读取
├── rag_api.py         # KG-RAG 知识库接口
├── llm_api.py         # 通用大模型接口（OpenAI Compatible）
├── judge.py           # 判题模块（提取选项、判断对错、按课程统计）
├── exporter.py        # Excel 导出模块（逐题明细 + 按课程汇总）
└── test_demo.py       # 主程序
```

## 流程

```
SQLite 题库 → 读取题目 → KG-RAG 接口  → 判题 → 控制台输出
                     → 通用 LLM 接口 → 判题 → JSON / Excel 保存
```

## 环境要求

- Python 3.8+
- 依赖包：`requests`, `openpyxl`
- 服务器上需运行 KG-RAG 服务（localhost:4103）
- 通用大模型接口需网络可达

```bash
pip install requests openpyxl
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

# 批量测试全部题目，保存到 results.json
python test_demo.py --batch

# 批量测试 + 导出 Excel
python test_demo.py --batch --export

# 批量测试 + 指定输出文件 + 导出 Excel
python test_demo.py --batch my_results.json --export
```

## 批量测试

`--batch` 模式遍历题库中所有题目，每道题分别调用 KG-RAG 和通用大模型，自动判断对错，保存结果。

### 进度显示

```
[INFO] 批量测试开始，共 500 道题

[1/500] Q#1 医学微生物学 ... 完成 (RAG=OK✓, LLM=OK✓, 4.2s)
[2/500] Q#2 生理学 ... 完成 (RAG=OK✗, LLM=OK✓, 3.8s)
```

进度行中 `✓` 表示该模型回答正确，`✗` 表示错误。

### 测试汇总

```
============================================================
  批量测试完成
============================================================
  总题数：500
  总耗时：2100.5s (35.0min)
  KG-RAG 失败：3 次
  通用 LLM 失败：0 次

  KG-RAG 正确率：452/500 = 90.40%
  通用LLM 正确率：478/500 = 95.60%
============================================================

--- 按课程正确率 ---
  病理学: RAG=88.50%  LLM=94.20%  (共120题)
  生理学: RAG=92.10%  LLM=97.30%  (共150题)
  药理学: RAG=89.70%  LLM=95.00%  (共100题)
  ...
```

### Excel 输出（--export）

导出文件包含 3 个 Sheet：

| Sheet | 内容 |
|-------|------|
| 逐题明细 | 每题题目、标准答案、KG-RAG/LLM回答、提取选项、对错标记 |
| 按课程汇总 | 各课程题目数、正确数、正确率，底部合计行 |
| 总体统计 | KG-RAG vs LLM 正确率对比、接口失败次数、总耗时 |

### results.json 结构

```json
{
  "test_time": "2026-06-29 16:00:00",
  "total_questions": 500,
  "rag_fail_count": 3,
  "llm_fail_count": 0,
  "total_time_s": 2100.5,
  "overall": {
    "total": 500,
    "rag_correct": 452,
    "llm_correct": 478,
    "rag_accuracy": 0.904,
    "llm_accuracy": 0.956
  },
  "by_course": [
    {"course": "生理学", "total": 150, "rag_correct": 138, ...}
  ],
  "results": [
    {
      "id": 1,
      "course": "医学微生物学",
      "question": "质粒是：\nA. ...\nB. ...",
      "answer": "A",
      "rag_answer": "A。质粒是细菌...",
      "llm_answer": "A。质粒存在于...",
      "rag_opt": "A",
      "llm_opt": "A",
      "rag_correct": true,
      "llm_correct": true,
      "rag_time": 4.2,
      "llm_time": 4.2,
      "rag_ok": true,
      "llm_ok": true
    }
  ]
}
```

### 判题逻辑

从模型回答文本中自动提取选项字母（A/B/C/D/E），匹配策略：

1. **显式标记** — 匹配「正确答案是B」「答案：C」「选A」等
2. **行首选项** — 匹配行首的「B。xxx」格式
3. **全文扫描** — 取最后出现的独立 A-E 字母

提取到的选项与标准答案比较，判断是否正确。

### 容错机制

单道题的 API 调用失败不会中断整个批量测试。失败题目的回答字段会标记 `[ERROR]`，判题结果自动判错。

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
...

标准答案：B

----------------------------------------
【KG-RAG】→ 提取选项: B | ✓ 正确
答案：B。根据教材内容，内环境即细胞外液...
(耗时 3.2s, 状态: OK)

----------------------------------------
【通用大模型】→ 提取选项: B | ✓ 正确
答案：B。细胞外液是机体内细胞直接生活的环境...
(耗时 1.8s, 状态: OK)
============================================================
```

## 部署到 Linux 服务器

```bash
# 上传 test/ 目录下全部文件
test/
├── config.py
├── db_reader.py
├── rag_api.py
├── llm_api.py
├── judge.py
├── exporter.py
└── test_demo.py

# 安装依赖
pip install requests openpyxl

# 运行
cd test
python test_demo.py --batch --export
```

## 版本计划

| 版本 | 功能 | 状态 |
|------|------|------|
| v1 | 单题/少量题测试，控制台输出 | ✅ 完成 |
| v2 | 遍历题库批量测试，JSON 保存，容错与进度显示 | ✅ 完成 |
| v3 | 自动判对错、按课程统计正确率、导出 Excel | ✅ 当前 |
| v4 | 多模型对比（Qwen/DeepSeek/GPT）、Prompt 对比、图表输出 | 📋 计划中 |
