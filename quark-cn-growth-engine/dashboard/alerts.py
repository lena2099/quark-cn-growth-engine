"""
预警与通知引擎
将关键事件实时推送到企业微信/飞书
"""
import json
import logging
from datetime import datetime
from typing import List, Dict

import httpx

logger = logging.getLogger("quark.dashboard.alerts")


class AlertEngine:
    """多渠道实时预警推送"""

    def __init__(self, config: dict):
        self.config = config
        self.notification_cfg = config["notifications"]
        self.alert_rules = self.notification_cfg["alert_rules"]

        self.wechat_webhook = self._get_env_or_config("WECHAT_WEBHOOK")
        self.feishu_webhook = self._get_env_or_config("FEISHU_WEBHOOK")

    def _get_env_or_config(self, key: str) -> str:
        """优先从环境变量获取Webhook URL"""
        import os
        return os.getenv(key, self.notification_cfg.get(f"{key.lower()}_webhook", ""))

    async def push_hot_leads(self, leads: List[Dict]) -> bool:
        """推送高分线索到企业微信"""
        if not self.wechat_webhook:
            logger.warning("WeChat webhook not configured, skipping push.")
            return False

        content = self._format_hot_leads_markdown(leads)
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": content},
        }

        return await self._send_wechat(payload)

    async def push_competitor_alerts(self, events: List[Dict]) -> bool:
        """推送竞品紧急预警"""
        if not self.wechat_webhook:
            return False

        content = self._format_competitor_alerts(events)
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": content},
        }

        return await self._send_wechat(payload)

    async def push_daily_signals(self, signals: List[Dict]) -> bool:
        """推送每日行业信号摘要"""
        if not self.wechat_webhook:
            return False

        content = self._format_daily_signals(signals)
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": content},
        }

        return await self._send_wechat(payload)

    async def push_daily_digest(self, report: Dict) -> bool:
        """推送每日线索摘要"""
        if not self.wechat_webhook:
            return False

        content = f"""## 📊 Quark CN Growth 日报
> {datetime.now().strftime('%Y-%m-%d')}

**线索Pipeline**
- 新发现线索: {report.get('new_leads', '—')}
- 高意向线索: {report.get('hot_leads', '—')}
- 待跟进线索: {report.get('pending_leads', '—')}

**渠道动态**
- 新签约: {report.get('new_signings', '—')}
- 洽谈中: {report.get('in_negotiation', '—')}

**品牌声量**
- 小红书: {report.get('xhs_mentions', '—')}
- 微信指数: {report.get('wechat_index', '—')}

> 详细报告: [查看看板](http://localhost:8501)
"""
        payload = {"msgtype": "markdown", "markdown": {"content": content}}
        return await self._send_wechat(payload)

    async def push_weekly_report(self, report: Dict) -> bool:
        """推送周报"""
        # 周报内容较多，通过看板链接+摘要方式推送
        content = f"""## 📈 Quark CN Growth 周报
> {report.get('week_range', '本周')}

**本周亮点**
{chr(10).join(f'- {h}' for h in report.get('highlights', ['暂无数据']))}

**关键指标**
| 指标 | 本周 | 较上周 |
|------|------|--------|
| 新线索 | {report.get('weekly_leads', '—')} | {report.get('leads_change', '—')} |
| 签约 | {report.get('weekly_signings', '—')} | {report.get('signings_change', '—')} |
| 预订 | {report.get('weekly_bookings', '—')} | {report.get('bookings_change', '—')} |

> [查看完整周报](http://localhost:8501)
"""
        payload = {"msgtype": "markdown", "markdown": {"content": content}}
        return await self._send_wechat(payload)

    # ═══════════════════════════════════════════════════════════════
    # 格式化方法
    # ═══════════════════════════════════════════════════════════════

    def _format_hot_leads_markdown(self, leads: List[Dict]) -> str:
        """格式化高分线索为企业微信 Markdown"""
        lines = [
            "## 🔥 高分渠道线索预警",
            f"> 发现 {len(leads)} 条高分线索（评分≥70）\n",
        ]

        for i, lead in enumerate(leads[:5], 1):  # 最多显示5条
            companies = lead.get("extracted_companies", [lead.get("company_name", "未知")])
            score = lead.get("score", 0)
            tier = lead.get("tier", "cold")
            tier_emoji = {"hot": "🔴", "warm": "🟡", "cold": "⚪"}.get(tier, "⚪")

            lines.append(
                f"{i}. {tier_emoji} **{companies[0]}** "
                f"[评分: {score}]"
            )
            if lead.get("source"):
                lines.append(f"   - 来源: {lead['source']}")
            if lead.get("url"):
                lines.append(f"   - [查看详情]({lead['url']})")

        if len(leads) > 5:
            lines.append(f"\n... 及其他 {len(leads) - 5} 条线索")

        lines.append(f"\n> 操作: [打开看板](http://localhost:8501)")
        return "\n".join(lines)

    def _format_competitor_alerts(self, events: List[Dict]) -> str:
        """格式化竞品预警"""
        lines = [
            "## ⚠️ 竞品动态预警",
            f"> {len(events)} 条需关注的竞品动态\n",
        ]

        for i, event in enumerate(events[:5], 1):
            urgency = event.get("urgency", "medium")
            urgency_emoji = {
                "critical": "🔴",
                "high": "🟡",
                "medium": "🟢",
            }.get(urgency, "⚪")

            lines.append(
                f"{i}. {urgency_emoji} **{event.get('competitor', '未知')}**"
            )
            lines.append(f"   - {event.get('title', '无详情')}")
            lines.append(f"   - 类型: {event.get('type', '未知')}")

        lines.append(f"\n> 操作: [打开看板](http://localhost:8501)")
        return "\n".join(lines)

    def _format_daily_signals(self, signals: List[Dict]) -> str:
        """格式化每日行业信号"""
        lines = [
            "## 📡 行业信号日报",
            f"> {datetime.now().strftime('%Y-%m-%d')}\n",
        ]

        for i, signal in enumerate(signals[:8], 1):
            impact = signal.get("impact", "neutral")
            impact_emoji = {
                "positive": "🟢",
                "negative": "🔴",
                "neutral": "⚪",
            }.get(impact, "⚪")

            lines.append(
                f"{i}. {impact_emoji} {signal.get('title', '无标题')}"
            )
            lines.append(f"   - {signal.get('summary', '')[:100]}")

        lines.append(f"\n> 操作: [打开看板](http://localhost:8501)")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # 发送方法
    # ═══════════════════════════════════════════════════════════════

    async def _send_wechat(self, payload: dict) -> bool:
        """发送企业微信 Webhook 消息"""
        if not self.wechat_webhook:
            return False

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.wechat_webhook, json=payload)
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get("errcode") == 0:
                        logger.info("WeChat notification sent successfully.")
                        return True
                    else:
                        logger.error(
                            f"WeChat notification failed: {result.get('errmsg')}"
                        )
                        return False
                else:
                    logger.error(f"WeChat notification HTTP {resp.status_code}")
                    return False
        except Exception as e:
            logger.error(f"WeChat notification error: {e}")
            return False

    async def _send_feishu(self, payload: dict) -> bool:
        """发送飞书 Webhook 消息"""
        if not self.feishu_webhook:
            return False

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.feishu_webhook, json=payload)
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Feishu notification error: {e}")
            return False
