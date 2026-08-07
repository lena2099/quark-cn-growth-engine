"""
日报生成器 — 将各 Agent 分析结果整合为可读报告
Report Generator v1.0

输出格式: Markdown / JSON / HTML Dashboard
"""

import os
import json
from datetime import date
from config.settings import REPORT_CONFIG, COMPETITOR_BRANDS


class ReportGenerator:
    """日报生成 — 整合所有 Agent 输出"""

    def generate(self, results: dict, report_date: date) -> list[str]:
        """
        输入: 各 Agent 的分析结果
        输出: 报告文件路径列表
        """
        report_dir = "data/reports"
        os.makedirs(report_dir, exist_ok=True)

        paths = []

        # Markdown 日报
        md_path = os.path.join(report_dir, f"daily_report_{report_date}.md")
        md_content = self._build_markdown(results, report_date)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        paths.append(md_path)

        # JSON 结构化数据
        json_path = os.path.join(report_dir, f"daily_report_{report_date}.json")
        # 只保留关键数据，避免文件过大
        compact = self._compact_results(results)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(compact, f, ensure_ascii=False, indent=2)
        paths.append(json_path)

        # HTML Dashboard
        html_path = os.path.join(report_dir, f"daily_report_{report_date}.html")
        html_content = self._build_html(results, report_date)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        paths.append(html_path)

        return paths

    # ── Markdown 报告 ──

    def _build_markdown(self, results: dict, report_date: date) -> str:
        """构建完整的 Markdown 日报"""
        sections = []

        # 标题
        sections.append(f"# 🐻‍❄️ Quark Expeditions 中国市场日报")
        sections.append(f"**{REPORT_CONFIG['subtitle']}**  |  {report_date}")
        sections.append("")
        sections.append("---")

        # 1. 今日市场概览
        radar = results.get("keyword_radar", {})
        social = results.get("social_media", {})
        intent = results.get("intent_analysis", {})
        brand = results.get("brand_monitor", {})

        sections.append("## 📊 今日市场概览")
        sections.append("")
        sections.append(f"- **关键词总提及量**: {radar.get('total_mentions', '-')}")
        sections.append(f"- **社媒总内容量**: {social.get('total_content', '-')}")
        sections.append(f"- **分析用户数**: {intent.get('analyzed_count', '-')}")
        sections.append(f"- **品牌相关内容**: {brand.get('total_branded_content', '-')}")
        sections.append("")

        # AI 概览
        ai_overview = radar.get("ai_analysis", "")
        if ai_overview:
            sections.append(f"> {ai_overview}")
            sections.append("")

        # 2. 关键词雷达
        if radar:
            sections.append("---")
            sections.append("## 🔍 关键词雷达")
            sections.append("")

            # 分类统计
            cat_breakdown = radar.get("category_breakdown", {})
            if cat_breakdown:
                sections.append("### 关键词类别分布")
                sections.append("")
                sections.append("| 类别 | 提及量 |")
                sections.append("|------|--------|")
                for cat, count in sorted(cat_breakdown.items(), key=lambda x: x[1], reverse=True):
                    sections.append(f"| {cat} | {count} |")
                sections.append("")

            # 飙升关键词
            surges = radar.get("surge_keywords", [])
            if surges:
                sections.append("### 🔥 热度飙升关键词")
                sections.append("")
                sections.append("| 关键词 | 热度变化 |")
                sections.append("|--------|----------|")
                for s in surges[:10]:
                    sections.append(f"| {s['keyword']} | +{s['change_pct']}% |")
                sections.append("")

            # 告警
            alerts = radar.get("alerts", [])
            if alerts:
                for alert in alerts:
                    sections.append(f"> {alert}")
                sections.append("")

        # 3. 社媒热榜
        if social:
            sections.append("---")
            sections.append("## 📱 社媒热榜")
            sections.append("")

            platform_data = social.get("platform_breakdown", {})
            for pk, pd in platform_data.items():
                sections.append(f"### {pd.get('name', pk)}")
                count = pd.get("content_count", 0)
                sections.append(f"内容量: **{count}**  |  点赞: **{pd.get('total_likes', 0)}**  |  评论: **{pd.get('total_comments', 0)}**")
                sections.append("")

                top_content = pd.get("top_content", [])
                if top_content:
                    sections.append("**热门内容 TOP 3:**")
                    sections.append("")
                    for i, tc in enumerate(top_content[:3], 1):
                        sections.append(
                            f"{i}. **{tc.get('author', '未知')}** — "
                            f"《{tc.get('title', '无标题')}》 "
                            f"(👍{tc.get('likes', 0)} 💬{tc.get('comments', 0)}) "
                            f"→ 用户意向: {tc.get('user_intent', '-')}"
                        )
                    sections.append("")

                # 评论关键词
                ck = pd.get("comment_keywords", [])
                if ck:
                    top_ck = ck[:5]
                    sections.append(f"💬 高频评论词: {'、'.join(k['keyword'] for k in top_ck)}")
                    sections.append("")

            # AI 摘要
            soc_summary = social.get("summary", "")
            if soc_summary:
                sections.append(f"> {soc_summary}")
                sections.append("")

        # 4. 用户意图洞察
        if intent:
            sections.append("---")
            sections.append("## 🧠 用户意图洞察")
            sections.append("")

            intent_dist = intent.get("intent_distribution", {})
            stage_dist = intent.get("stage_distribution", {})

            sections.append(f"**分析总量**: {intent.get('analyzed_count', 0)} 条用户内容")
            sections.append("")

            if intent_dist:
                sections.append("### 购买意图分布")
                sections.append("")
                sections.append("| 意图等级 | 数量 |")
                sections.append("|----------|------|")
                for level, cnt in sorted(intent_dist.items(), key=lambda x: x[1], reverse=True):
                    sections.append(f"| {level} | {cnt} |")
                sections.append("")

            if stage_dist:
                sections.append("### 购买阶段分布")
                sections.append("")
                sections.append("| 阶段 | 数量 |")
                sections.append("|------|------|")
                for stage, cnt in sorted(stage_dist.items(), key=lambda x: x[1], reverse=True):
                    sections.append(f"| {stage} | {cnt} |")
                sections.append("")

            # 用户画像
            profile = intent.get("profile_distribution", {})
            if profile:
                sections.append("### 用户画像分布")
                sections.append("")
                for label, dist in profile.items():
                    top3 = sorted(dist.items(), key=lambda x: x[1], reverse=True)[:3]
                    sections.append(f"- **{label}**: {' | '.join(f'{k}({v})' for k, v in top3)}")
                sections.append("")

            # 高意图用户
            high_intent = intent.get("high_intent_users", [])
            if high_intent:
                sections.append("### 🎯 高购买意图用户")
                sections.append("")
                for i, user in enumerate(high_intent[:5], 1):
                    sections.append(
                        f"{i}. {user.get('age_group', '-')} {user.get('gender', '-')} — "
                        f"关注: {user.get('core_concern', '-')} — "
                        f"建议: {user.get('recommended_action', '-')}"
                    )
                sections.append("")

            strategy = intent.get("strategy_suggestions", "")
            if strategy:
                sections.append(f"> 📝 **策略建议**: {strategy}")
                sections.append("")

        # 5. 品牌声量监测
        if brand:
            sections.append("---")
            sections.append("## 📊 品牌声量监测")
            sections.append("")

            own = brand.get("own_brand", {})
            sections.append(f"### 夸克探险 (Quark Expeditions)")
            sections.append("")
            sections.append(f"- **声量占比 (SOV)**: **{own.get('sov_pct', '-')}%** (变化: {own.get('sov_change_pct', 0):+.1f}%)")
            sections.append(f"- **行业排名**: 第 {own.get('ranking', '-')} 位")
            sections.append(f"- **提及次数**: {own.get('mentions', '-')}")
            sections.append("")

            sentiment = own.get("sentiment", {})
            if sentiment:
                total_s = sum(sentiment.values()) or 1
                sections.append(
                    f"情感分析: 正面 {sentiment.get('positive', 0)} "
                    f"({round(sentiment['positive']/total_s*100)}%) | "
                    f"中性 {sentiment.get('neutral', 0)} | "
                    f"负面 {sentiment.get('negative', 0)}"
                )
                sections.append("")

            # 竞品排名
            comp_ranking = brand.get("competitor_ranking", [])
            if comp_ranking:
                sections.append("### 竞品声量排名")
                sections.append("")
                sections.append("| 品牌 | 提及量 | SOV | 情感倾向 |")
                sections.append("|------|--------|-----|----------|")
                for c in comp_ranking:
                    own_marker = " ⭐" if c.get("is_own") else ""
                    sent = c.get("sentiment", {})
                    pos = sent.get("positive", 0)
                    neg = sent.get("negative", 0)
                    if pos > neg:
                        sent_str = "正面为主 ✅"
                    elif neg > pos:
                        sent_str = "有负面 ⚠️"
                    else:
                        sent_str = "中性"
                    sections.append(
                        f"| **{c['name']}**{own_marker} | {c['mentions']} | {c['sov']}% | {sent_str} |"
                    )
                sections.append("")

            health = brand.get("brand_health", "")
            if health:
                sections.append(f"> 🩺 **品牌健康度**: {health}")
                sections.append("")

            brand_alerts = brand.get("alerts", [])
            if brand_alerts:
                for alert in brand_alerts:
                    sections.append(f"> {alert}")
                sections.append("")

        # 6. 市场机会与建议
        sections.append("---")
        sections.append("## 💡 今日市场机会与建议")
        sections.append("")
        sections.append("_本报告由 Polar Market Intelligence Agent 自动生成。_")
        sections.append(f"_生成时间: {report_date} 次日 08:00 CST_")
        sections.append("")

        return "\n".join(sections)

    # ── HTML Dashboard ──

    def _build_html(self, results: dict, report_date: date) -> str:
        """构建 HTML Dashboard"""
        radar = results.get("keyword_radar", {})
        social = results.get("social_media", {})
        intent = results.get("intent_analysis", {})
        brand = results.get("brand_monitor", {})

        own = brand.get("own_brand", {})
        surges = radar.get("surge_keywords", [])[:10]
        comp_ranking = brand.get("competitor_ranking", [])

        # 构建 HTML
        surges_html = "".join(
            f'<tr><td>{s["keyword"]}</td><td class="up">+{s["change_pct"]}%</td></tr>'
            for s in surges
        ) if surges else '<tr><td colspan="2">暂无数据</td></tr>'

        comp_html = "".join(
            f'<tr class="{"own" if c.get("is_own") else ""}">'
            f'<td>{"⭐ " if c.get("is_own") else ""}{c["name"]}</td>'
            f'<td>{c["mentions"]}</td><td>{c["sov"]}%</td></tr>'
            for c in comp_ranking
        ) if comp_ranking else '<tr><td colspan="3">暂无数据</td></tr>'

        alerts_all = radar.get("alerts", []) + brand.get("alerts", [])
        alerts_html = "".join(
            f'<div class="alert">{a}</div>' for a in alerts_all
        ) if alerts_all else ""

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Quark 中国市场日报 — {report_date}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; color: #1a1a2e; padding: 1.5rem; }}
.container {{ max-width: 1000px; margin: 0 auto; }}
.header {{ background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: white; border-radius: 16px; padding: 2rem; margin-bottom: 1.5rem; }}
.header h1 {{ font-size: 1.8rem; font-weight: 700; }}
.header .sub {{ opacity: 0.85; margin-top: 0.5rem; font-size: 0.95rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }}
.card {{ background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.card h3 {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem; }}
.card .value {{ font-size: 2rem; font-weight: 700; color: #0f2027; }}
.card .change {{ font-size: 0.85rem; margin-top: 0.25rem; }}
.up {{ color: #16a34a; }}
.down {{ color: #dc2626; }}
.section {{ background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.section h2 {{ font-size: 1.2rem; margin-bottom: 1rem; color: #0f2027; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #f1f5f9; }}
th {{ font-size: 0.8rem; color: #64748b; font-weight: 600; }}
tr.own {{ background: #f0f9ff; font-weight: 600; }}
.footer {{ text-align: center; color: #94a3b8; font-size: 0.8rem; margin-top: 2rem; }}
.alert {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 0.75rem; border-radius: 0 8px 8px 0; margin: 0.5rem 0; font-size: 0.9rem; }}
.tag {{ display: inline-block; padding: 0.15rem 0.6rem; border-radius: 100px; font-size: 0.75rem; margin-right: 0.3rem; }}
.tag-green {{ background: #dcfce7; color: #166534; }}
.tag-yellow {{ background: #fef9c3; color: #854d0e; }}
.tag-red {{ background: #fee2e2; color: #991b1b; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>🐻‍❄️ Quark Expeditions 中国市场日报</h1>
  <div class="sub">Polar Market Intelligence Agent | {report_date} | 自动生成</div>
</div>

<div class="grid">
  <div class="card">
    <h3>关键词提及量</h3>
    <div class="value">{radar.get('total_mentions', '-')}</div>
  </div>
  <div class="card">
    <h3>社媒总内容</h3>
    <div class="value">{social.get('total_content', '-')}</div>
  </div>
  <div class="card">
    <h3>分析用户</h3>
    <div class="value">{intent.get('analyzed_count', '-')}</div>
  </div>
  <div class="card">
    <h3>夸克 SOV</h3>
    <div class="value">{own.get('sov_pct', '-')}%</div>
    <div class="change {'up' if own.get('sov_change_pct', 0) >= 0 else 'down'}">变化: {own.get('sov_change_pct', 0):+.1f}%</div>
  </div>
</div>

{alerts_html or ''}

<div class="section">
  <h2>🔥 热度飙升关键词</h2>
  <table><tr><th>关键词</th><th>热度变化</th></tr>{surges_html}</table>
</div>

<div class="section">
  <h2>📊 品牌声量排名</h2>
  <table><tr><th>品牌</th><th>提及量</th><th>SOV</th></tr>{comp_html}</table>
</div>

<div class="section">
  <h2>🧠 用户意图分布</h2>
  <table><tr><th>意图等级</th><th>数量</th></tr>
  {"".join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k,v in intent.get('intent_distribution', {}).items())}
  </table>
</div>

<div class="footer">
  Polar Market Intelligence Agent · 每日 08:00 CST 自动更新 · Powered by AI
</div>

</div>
</body>
</html>"""
        return html

    # ── 压缩输出 ──

    def _compact_results(self, results: dict) -> dict:
        """生成压缩版 JSON，方便后续程序消费"""
        radar = results.get("keyword_radar", {})
        brand = results.get("brand_monitor", {})
        intent = results.get("intent_analysis", {})

        return {
            "report_date": results.get("report_date"),
            "summary": {
                "total_mentions": radar.get("total_mentions", 0),
                "total_content": results.get("social_media", {}).get("total_content", 0),
                "analyzed_users": intent.get("analyzed_count", 0),
                "quark_sov": brand.get("own_brand", {}).get("sov_pct", 0),
                "quark_ranking": brand.get("own_brand", {}).get("ranking", "-"),
            },
            "surge_keywords": [s["keyword"] for s in radar.get("surge_keywords", [])],
            "alerts": radar.get("alerts", []) + brand.get("alerts", []),
            "competitor_ranking": [
                {"name": c["name"], "sov": c["sov"], "mentions": c["mentions"]}
                for c in brand.get("competitor_ranking", [])
            ],
            "intent_distribution": intent.get("intent_distribution", {}),
            "strategy": intent.get("strategy_suggestions", ""),
        }
