# Polar Market Intelligence Agent

## 🐻‍❄️ 极地市场智能情报系统

每天自动回答：
- 中国用户最近在关注什么南极相关内容？
- 哪些平台增长最快？
- 用户有哪些购买意图？
- 夸克探险曝光占比多少？
- 竞争品牌是谁？
- 下一步营销应该做什么？

---

## 架构

```
数据采集层 (人工导入 CSV/JSON)
         ↓
  ┌──────┼────────┬──────────┐
  ↓      ↓        ↓          ↓
关键词  社媒    用户意图   品牌监测
雷达    热榜    分析       竞品SOV
  └──────┼────────┴──────────┘
         ↓
   日报生成 (MD / JSON / HTML)
         ↓
   分发 (企微 / 邮件)
```

## 四个 AI Agent

| Agent | 功能 |
|-------|------|
| 🔍 **KeywordRadar** | 三级关键词热度监控、飙升检测、趋势分析 |
| 📱 **SocialMedia** | 多平台内容热榜、评论意图检测、创作者发现 |
| 🧠 **IntentAnalyzer** | GPT 驱动的用户画像提取、购买意图评级、营销建议 |
| 📊 **BrandMonitor** | 夸克 SOV 计算、竞品排名、品牌健康度分析 |

## 自动化工作流

- **时间**: 北京时间每天早上 8:00
- **触发**: GitHub Actions cron (`0 0 * * *` UTC)
- **流程**: 数据读取 → Agent 分析 → 报告生成 → 推送

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 设置 DeepSeek API Key
export DEEPSEEK_API_KEY="sk-..."

# 运行完整流程 (自动生成模拟数据)
python main.py

# 查看报告
open data/reports/daily_report_*.html
```

## 数据输入格式

MVP 阶段使用 CSV/JSON 人工导入，格式:

```csv
date,platform,keyword,title,link,likes,comments,saves,author,content,comments_content
2026-08-06,xiaohongshu,南极旅游,南极攻略,https://...,120,30,50,旅行者小美,想去南极很久了...,多少钱|求攻略
```

## GitHub Secrets 配置

在仓库 Settings → Secrets and variables → Actions 中设置:

| Secret | 说明 |
|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 (必需, 从 platform.deepseek.com 获取) |
| `WECHAT_WEBHOOK` | 企业微信 Webhook (可选) |
| `EMAIL_*` | 邮件发送配置 (可选) |

## 项目结构

```
polar-intelligence-agent/
├── .github/workflows/
│   └── daily-market-report.yml    # 每日自动工作流
├── agents/
│   ├── keyword_radar.py           # 关键词雷达
│   ├── social_media.py            # 社媒热榜
│   ├── intent_analyzer.py         # 用户意图分析
│   ├── brand_monitor.py           # 品牌声量监测
│   └── report_generator.py        # 日报生成
├── config/
│   └── settings.py                # 全局配置
├── scripts/
│   └── generate_mock_data.py      # 模拟数据生成
├── data/
│   ├── raw/                       # 原始数据
│   ├── processed/                 # 中间结果
│   └── reports/                   # 日报输出
├── main.py                        # 主入口
├── requirements.txt
└── README.md
```
