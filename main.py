"""
极地市场智能情报系统 — 主编排入口
Polar Market Intelligence Agent v1.0

每日工作流:
  1. 关键词雷达 Agent → 热度变化分析
  2. 社媒数据 Agent → 多平台内容采集 & 摘要
  3. 用户意图 Agent → AI 驱动的购买意图洞察
  4. 品牌监测 Agent → 夸克探险曝光占比 & 竞品分析
  5. 日报生成 → 《Quark 中国市场日报》
"""

import os
import sys
import json
from datetime import date, datetime, timedelta

from agents.keyword_radar import KeywordRadarAgent
from agents.social_media import SocialMediaAgent
from agents.intent_analyzer import IntentAnalyzerAgent
from agents.brand_monitor import BrandMonitorAgent
from agents.report_generator import ReportGenerator


def main():
    # 确定分析日期: 默认昨天 (因为今天的数据可能不完整)
    report_date_str = os.environ.get("REPORT_DATE", "")
    if report_date_str:
        report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
    else:
        report_date = date.today() - timedelta(days=1)

    report_type = os.environ.get("REPORT_TYPE", "full")
    print(f"\n{'='*60}")
    print(f"  🐻‍❄️  Polar Market Intelligence Agent")
    print(f"  分析日期: {report_date} | 报告类型: {report_type}")
    print(f"{'='*60}\n")

    # ── 第一阶段: 数据采集 ──
    # 从 data/raw/ 读取人工导入的 CSV 或上一阶段采集的数据
    raw_data = _load_raw_data(report_date)

    if not raw_data:
        print("⚠️  未找到当日原始数据, 尝试生成模拟数据用于流程验证...")
        from scripts.generate_mock_data import generate_mock_data
        raw_data = generate_mock_data(report_date)

    # ── 第二阶段: Agent 分析 ──
    results: dict[str, any] = {"report_date": str(report_date)}

    # Agent 1: 关键词雷达
    if report_type in ("full", "keyword-only"):
        print("[1/4] 🔍 关键词雷达 Agent 启动...")
        radar = KeywordRadarAgent()
        results["keyword_radar"] = radar.analyze(raw_data, report_date)

    # Agent 2: 社媒数据采集
    if report_type == "full":
        print("[2/4] 📱 社媒数据 Agent 启动...")
        social = SocialMediaAgent()
        results["social_media"] = social.analyze(raw_data, report_date)

    # Agent 3: 用户意图分析
    if report_type == "full":
        print("[3/4] 🧠 用户意图分析 Agent 启动...")
        intent = IntentAnalyzerAgent()
        results["intent_analysis"] = intent.analyze(raw_data, report_date)

    # Agent 4: 品牌曝光监测
    if report_type in ("full", "brand-only"):
        print("[4/4] 📊 品牌监测 Agent 启动...")
        monitor = BrandMonitorAgent()
        results["brand_monitor"] = monitor.analyze(raw_data, report_date)

    # ── 第三阶段: 报告生成 ──
    print("\n📝 生成日报...")
    generator = ReportGenerator()
    report_paths = generator.generate(results, report_date)

    # ── 第四阶段: 分发 ──
    _send_report(report_paths)

    print(f"\n✅ 完成! 报告输出:")
    for path in report_paths:
        print(f"   📄 {path}")


def _load_raw_data(report_date: date) -> list[dict] | None:
    """从 data/raw/ 加载指定日期的原始数据"""
    raw_dir = "data/raw"
    target_file = os.path.join(raw_dir, f"{report_date}.json")
    csv_file = os.path.join(raw_dir, f"{report_date}.csv")

    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)

    if os.path.exists(csv_file):
        import csv
        with open(csv_file, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    return None


def _send_report(report_paths: list[str]) -> None:
    """发送报告到邮件/企微"""
    wechat_webhook = os.environ.get("WECHAT_WEBHOOK", "")
    if wechat_webhook and report_paths:
        # 找到 markdown 报告
        md_reports = [p for p in report_paths if p.endswith(".md")]
        if md_reports:
            with open(md_reports[0], "r", encoding="utf-8") as f:
                content = f.read()[:4000]  # 企微消息有长度限制
            try:
                import requests
                requests.post(wechat_webhook, json={
                    "msgtype": "markdown",
                    "markdown": {"content": content}
                }, timeout=10)
                print("📨 已发送到企业微信")
            except Exception as e:
                print(f"⚠️  企微发送失败: {e}")


if __name__ == "__main__":
    main()
