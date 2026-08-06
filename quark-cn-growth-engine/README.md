# Quark Expeditions 中国市场增长引擎 (Quark CN Growth Engine)

> **7×24小时自动化获客系统** — 为 Quark Expeditions（夸克探险）中国市场团队定制的增长基础设施

## 🎯 定位

本系统是《Quark Expeditions 中国市场增长100天计划》的技术支撑层，提供：

- 🔍 **自动渠道伙伴发现** — 从旅游媒体、社交媒体、搜索引擎自动识别潜在B2B合作伙伴
- 👥 **领英/脉脉联系人采集** — 获取目标公司关键决策人的公开联系方式
- 🏴‍☠️ **竞品动态实时监控** — 追踪庞洛、银海、66度等竞品的中国市场动向
- 📡 **行业趋势雷达** — 捕获政策、市场、航线、投融资信号
- 📊 **实时数据看板** — Streamlit 可视化 Pipeline/KPI/竞品动态
- 📱 **企业微信/飞书预警推送** — 高分线索、竞品异动实时通知

## 🚀 快速启动

### 前置条件

- Docker & Docker Compose
- Python 3.11+（本地开发可选）

### 一键部署

```bash
# 1. 克隆/进入项目目录
cd quark-cn-growth-engine

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入必要参数

# 3. 启动所有服务
docker-compose up -d

# 4. 查看运行状态
docker-compose logs -f engine

# 5. 打开数据看板
open http://localhost:8501
```

### 本地开发运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动调度引擎（前台运行）
python scheduler.py

# 单独启动看板
streamlit run dashboard/app.py
```

## 📁 项目结构

```
quark-cn-growth-engine/
├── scheduler.py                  # 🎯 总调度器（入口）
├── docker-compose.yml            # Docker 一键部署
├── Dockerfile
├── requirements.txt
├── .env.example
│
├── config/
│   ├── settings.yaml             # ⚙️ 全局配置（调度/采集/评分/通知）
│   └── targets.yaml              # 🎯 目标合作伙伴清单（20家公司+联系人角色）
│
├── collectors/                   # 📥 数据采集层
│   ├── channel_discovery.py      # Workflow 1: 渠道伙伴发现引擎
│   ├── social_listener.py        # 社交媒体监听
│   ├── competitor_tracker.py     # Workflow 3: 竞品动态监控
│   └── industry_radar.py         # Workflow 4: 行业趋势雷达
│
├── processors/                   # 🔄 数据处理层
│   ├── lead_scorer.py            # 线索评分引擎（100分制多维模型）
│   └── dedup.py                  # 去重引擎（ID/公司名/URL三级去重）
│
├── outreach/                     # 📤 外联触达层
│   ├── linkedin_connector.py     # Workflow 2A: 领英公开联系人采集
│   ├── maimai_connector.py       # Workflow 2B: 脉脉公开名片采集
│   └── (email_automation.py)     # （待实现）邮件自动化触达
│
├── content/                      # 📝 内容引擎
│   └── distribution.py           # Workflow 5: 多平台内容分发
│
├── dashboard/                    # 📊 数据看板
│   ├── app.py                    # Streamlit 看板（6个页面）
│   └── alerts.py                 # 企业微信/飞书实时预警
│
├── database/                     # 🗄️ 数据层
│   └── (models.py, migrations/)  # SQLAlchemy ORM 模型
│
└── utils/                        # 🔧 工具层
    ├── config.py                 # YAML配置加载 + 环境变量注入
    ├── db.py                     # 数据库连接管理
    └── logging_config.py         # 日志配置
```

## ⏱️ 调度概览

| 工作流 | 频率 | 说明 |
|--------|------|------|
| 渠道伙伴发现 | 每日 06:00 | 扫描旅游媒体/搜索/社交媒体 |
| 领英联系人采集 | 每日 05:00/13:00/21:00 | 三轮扫描覆盖不同时区活跃度 |
| 竞品动态监控 | 每6小时 | 追踪新产品/定价/合作/招聘 |
| 行业趋势雷达 | 每日 08:00 | 政策/报告/航线/投融资 |
| 内容分发 | 每日 09:00/15:00/21:00 | 微信/小红书/知乎/领英 |
| 线索评分更新 | 每2小时 | 多维度自动评分 |
| 日报生成 | 每日 07:00 | 推送至企业微信 |
| 周报生成 | 每周一 09:00 | 综合KPI周报 |

## 📊 线索评分模型

| 维度 | 权重 | 评分标准 |
|------|------|----------|
| 资质认证 | 50分 | IAATO成员 +30, AECO成员 +20, 双认证 +5 |
| 业务规模 | 25分 | 产品线数量 + 年极地客量 |
| 品牌契合度 | 15分 | 提及Quark +8, 高端定位 +4, 探险/专业 +3 |
| 活跃信号 | 10分 | 近期动态 +5, 社交活跃 +3, 内容更新 +2 |

**线索等级**: 🔴 Hot (≥70) | 🟡 Warm (40-69) | ⚪ Cold (<40)

## ⚠️ 合规说明

本系统设计严格遵循以下合规原则：

- 仅采集**公开可索引**的信息
- 不绕过任何平台的反爬机制
- 不使用虚假账号或自动化登录
- 遵守 robots.txt 和请求频率限制
- 符合《个人信息保护法》(PIPL) — 仅存储业务联系方式
- 符合 GDPR — 不存储欧洲居民个人数据

> 建议初期以**手动搜索+录入为主**，自动化作为辅助和汇总工具。

## 📋 配合文档

- [《Quark Expeditions 中国市场增长100天计划》](../Quark_Expeditions_China_100Day_Growth_Plan.md) — 战略文档
- [config/targets.yaml](config/targets.yaml) — 20家目标合作伙伴及搜索角色清单
- [config/settings.yaml](config/settings.yaml) — 全部可调参数

## 🔄 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| 调度 | APScheduler (AsyncIO) |
| HTTP | httpx |
| 数据库 | PostgreSQL 16 + Redis 7 |
| ORM | SQLAlchemy 2.0 (async) |
| NLP | jieba (中文) / spaCy (英文) |
| 看板 | Streamlit + Plotly |
| 部署 | Docker Compose |
| 通知 | 企业微信/飞书 Webhook |

---

> **Built for Quark Expeditions China Growth** | 2026年8月
