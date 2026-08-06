# Polar Growth OS — 统一架构文档 v2.0

> 合并 Polar Growth OS 设计文档 + Quark CN Growth Engine 实现
> 日期：2026-08-07

---

## 架构演进：从 B2B 管道到 AI 增长操作系统

```
v1.0 (原始方案)              v2.0 (Polar Growth OS)
─────────────────────       ─────────────────────────
B2B渠道抓取                  四层 AI Agent 协作
关键词匹配                   意图识别 + 语义理解
固定评分规则                 LLM 驱动画像
手动跟单                     AI 销售教练
单机脚本                     pgvector + RAG + Agent 编排
```

---

## 一、四层架构

```
                        Polar Growth OS
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                     │
   客户洞察层             渠道拓展层             内容营销层           销售赋能层
 (Customer Intel)      (Channel BD)          (Content Engine)    (Sales Enable)
        │                    │                     │                   │
   ┌────┴────┐          ┌────┴────┐          ┌────┴────┐          ┌────┴────┐
  AI CRM   画像引擎    AI BD   渠道评分     AI选题   多端适配   AI话术   模拟对练
  + 客户360 + 流失预警  + 合伙人发现          + AB测试             + 异议处理
  + 交叉推荐             + 话术武器库          + 客户旅程内容         + 跟单助手
        │                    │                     │                   │
        └────────────────────┼─────────────────────┘                   │
                             │                                         │
                    ┌────────┴────────┐                               │
                    │   AI Agent 层    │                               │
                    │  ┌────────────┐  │                               │
                    │  │LangChain   │  │ ← GPT-4o / GPT-4o-mini       │
                    │  │编排引擎     │  │                               │
                    │  ├────────────┤  │                               │
                    │  │Agent 调度器 │  │ ← 多 Agent 协作               │
                    │  ├────────────┤  │                               │
                    │  │Prompt 模板库│  │ ← 8 套专业提示词              │
                    │  └────────────┘  │                               │
                    └────────┬────────┘                               │
                             │
                    ┌────────┴────────┐
                    │   向量数据库      │
                    │   pgvector       │ ← 客户语义检索 / RAG
                    └─────────────────┘
```

---

## 二、模块映射：文档 → 代码

| Polar Growth OS 文档 | 实现文件 | 状态 |
|---------------------|---------|------|
| **2.1 客户洞察 — AI CRM** | `collectors/polar_radar/scanner.py` + `agents/orchestrator.py` | ✅ |
| RFM 客户分层 | `scanner.py` → `_calculate_score()` | ✅ |
| 兴趣图谱 | `scanner.py` → `_infer_profile()` | ✅ |
| 流失预警 | `crm_agent/` | 📋 待实现 |
| 交叉推荐 | `vector_store/rag.py` → `recommend_content()` | ✅ |
| **2.2 渠道拓展 — AI BD** | `collectors/channel_discovery.py` + `agents/orchestrator.py` | ✅ |
| 渠道评级矩阵 | `config/targets.yaml`（20家）+ `orchestrator.py` → `score_channel()` | ✅ |
| 合伙人发现 | `channel_discovery.py`（多源扫描） | ✅ |
| 话术武器库 | `config/intent_patterns.yaml`（120+ 模式） | ✅ |
| 漏斗追踪 | `dashboard/app.py` | ✅ |
| **2.3 内容营销 — AI 内容引擎** | `collectors/polar_radar/nurture.py` + `agents/orchestrator.py` | ✅ |
| 选题雷达 | `orchestrator.py` → `generate_content_brief()` | ✅ |
| 多形态生成 | `orchestrator.py` → `adapt_content_multiformat()` | ✅ |
| 客户旅程内容 | `nurture.py` → 5 阶段内容库 | ✅ |
| A/B 测试 | `orchestrator.py` → `generate_ab_test()` | ✅ |
| **2.4 销售赋能 — AI 销售教练** | `sales_coach/coach.py` | ✅ |
| 实时话术提示 | `coach.py` → `handle_objection()` | ✅ |
| 异议处理库 | `coach.py` → 5 大类 50+ 异议框架 | ✅ |
| 模拟对练 | `coach.py` → `score_sales_response()` | ✅ |
| 跟单助手 | `coach.py` → `generate_followup()` | ✅ |
| **MVP 技术实现路线图** | `agents/orchestrator.py` | ✅ |
| LangChain + GPT API | `orchestrator.py` | ✅ |
| FastAPI 后端 | `orchestrator.py`（可包装 FastAPI） | 📋 |
| PostgreSQL + pgvector | `vector_store/rag.py` | ✅ |
| Streamlit 前端 | `dashboard/app.py` | ✅ |
| **Polar Customer Radar** | `collectors/polar_radar/` | ✅ |
| 意图识别 Agent | `scanner.py` | ✅ |
| Polar Score 评分 | `scanner.py` → `_calculate_score()` | ✅ |
| 五步培育路径 | `nurture.py` | ✅ |
| 微信标签体系 | `nurture.py` → `_generate_wecom_tags()` | ✅ |
| 视频号/抖音内容策略 | `nurture.py` → CONTENT_LIBRARY | ✅ |

---

## 三、核心数据流

```
                   ┌─────────────────────────────────────┐
                   │          数据采集层                   │
                   │                                     │
                   │  小红书 抖音 视频号 微信 领英 脉脉    │
                   │      ↓       ↓       ↓      ↓       │
                   │  channel_discovery.py               │
                   │  polar_radar/scanner.py             │
                   │  competitor_tracker.py              │
                   └──────────────┬──────────────────────┘
                                  │
                   ┌──────────────▼──────────────────────┐
                   │         AI Agent 编排层               │
                   │                                      │
                   │  orchestrator.py                     │
                   │  ┌──────────────────────────────┐   │
                   │  │ analyze_customer()            │   │
                   │  │ score_channel()               │   │
                   │  │ generate_talking_points()     │   │
                   │  │ generate_content_brief()      │   │
                   │  │ handle_objection()            │   │
                   │  └──────────────────────────────┘   │
                   └──────────────┬──────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────▼──────┐   ┌────────────▼────────┐   ┌─────────▼──────┐
│ 评分 & 画像     │   │  培育 & 触达          │   │ 销售赋能         │
│                │   │                      │   │                  │
│ lead_scorer.py │   │ nurture.py           │   │ coach.py         │
│ scanner.py     │   │ ┌──────────────────┐ │   │ ┌──────────────┐ │
│ rag.py         │   │ │ 5阶段旅程         │ │   │ │ 异议处理库    │ │
│                │   │ │ 内容推荐          │ │   │ │ 跟单消息      │ │
│                │   │ │ 触达时间表        │ │   │ │ 模拟评分      │ │
│                │   │ │ 微信标签          │ │   │ │ RAG增强       │ │
│                │   │ └──────────────────┘ │   │ └──────────────┘ │
└────────────────┘   └─────────────────────┘   └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                   ┌──────────────▼──────────────────────┐
                   │         持久化 & 可视化               │
                   │                                      │
                   │  PostgreSQL + pgvector + Redis       │
                   │  dashboard/app.py (Streamlit)        │
                   │  index.html (GitHub Pages)           │
                   │  企业微信/飞书 Webhook 通知            │
                   └──────────────────────────────────────┘
```

---

## 四、部署架构

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Engine      │  │  Dashboard   │  │  PostgreSQL  │  │
│  │  (scheduler)  │  │  (Streamlit) │  │  + pgvector  │  │
│  │  Port: —      │  │  Port: 8501  │  │  Port: 5432  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  ┌──────────────┐                                        │
│  │    Redis      │                                       │
│  │   Port: 6379  │                                       │
│  └──────────────┘                                        │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  外部服务 (需 API Key)                            │    │
│  │  · OpenAI GPT-4o (分析/生成)                      │    │
│  │  · OpenAI text-embedding-3-small (向量嵌入)       │    │
│  │  · 企业微信 Webhook (通知)                        │    │
│  │  · 飞书 Webhook (通知)                            │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 启动

```bash
# 完整部署
docker-compose up -d

# 仅运行演示（无需 API key）
python3 collectors/polar_radar/scanner.py    # 意图雷达
python3 collectors/polar_radar/nurture.py    # 培育引擎
python3 sales_coach/coach.py                  # 销售教练
python3 vector_store/rag.py                   # RAG 检索
python3 agents/orchestrator.py                # Agent 编排

# HTML 看板
open https://lena2099.github.io/quark-cn-growth-engine/
```

### 激活 GPT-4o

```bash
export OPENAI_API_KEY=sk-xxx
# 取消 agents/orchestrator.py 中的模拟返回注释
```

---

## 五、关键指标

| 维度 | 指标 | v1.0 基线 | v2.0 目标（3个月） |
|------|------|-----------|-------------------|
| **效率** | 单个客户分析时间 | 30 分钟 | **2 分钟** |
| **转化** | AI 推荐触达客户转化率 | 基线 | **+20%** |
| **覆盖** | 高价值客户标签覆盖率 | <30% | **>80%** |
| **内容** | 周均内容产出量 | 3 篇 | **15 篇** |
| **复购** | 老客户升级/复购率 | 基线 | **+15%** |
| **销售** | 异议解决时间 | 平均 30 分钟 | **实时（<10秒）** |

---

## 六、文件清单

```
quark-cn-growth-engine/
├── 📄 战略文档
│   └── Quark_Expeditions_China_100Day_Growth_Plan.md  (41KB)
│
├── 🧠 AI Agent 编排层
│   └── agents/orchestrator.py        # GPT-4o 编排 + 8套Prompt
│
├── 🎯 客户洞察层
│   ├── collectors/polar_radar/scanner.py    # 意图识别 + Polar Score
│   ├── collectors/polar_radar/nurture.py    # 5阶段培育 + 微信标签
│   ├── config/intent_patterns.yaml          # 120+ 意图模式
│   └── processors/lead_scorer.py            # B2B线索评分
│
├── 🔍 渠道拓展层
│   ├── collectors/channel_discovery.py      # 渠道伙伴发现
│   ├── collectors/competitor_tracker.py     # 竞品监控
│   ├── collectors/industry_radar.py         # 行业雷达
│   ├── outreach/linkedin_connector.py       # 领英采集
│   ├── outreach/maimai_connector.py         # 脉脉采集
│   └── config/targets.yaml                  # 20家目标伙伴
│
├── 💬 销售赋能层
│   └── sales_coach/coach.py                # 异议处理 + 跟单 + 模拟
│
├── 🎨 内容引擎层
│   └── content/distribution.py             # 多平台内容分发
│
├── 🔮 数据 & RAG
│   └── vector_store/rag.py                 # pgvector RAG
│
├── 📊 可视化
│   ├── dashboard/app.py                    # Streamlit 看板
│   ├── dashboard/alerts.py                 # 企业微信通知
│   └── index.html                          # GitHub Pages 看板
│
└── 🚀 部署
    ├── docker-compose.yml
    ├── Dockerfile
    └── requirements.txt
```

---

> **版本**：v2.0 | **日期**：2026-08-07
> **GitHub**：https://github.com/lena2099/quark-cn-growth-engine
> **在线看板**：https://lena2099.github.io/quark-cn-growth-engine/
