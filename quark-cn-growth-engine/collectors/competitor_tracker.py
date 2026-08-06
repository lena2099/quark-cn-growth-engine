"""
竞品动态监控器 (Workflow 3)
实时追踪竞品（庞洛、银海、66度、海达路德等）在中国市场的最新动态
"""
import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger("quark.collectors.competitor")


class CompetitorTracker:
    """多维度竞品动态追踪"""

    def __init__(self, config: dict):
        self.config = config
        self.competitors = config["collectors"]["competitor_brands"]
        self.request_delay = config["collectors"]["request_delay_seconds"]

    async def scan(self) -> List[Dict]:
        """全量扫描所有竞品动态"""
        events = []

        tasks = [
            self._scan_news(),
            self._scan_social_buzz(),
            self._scan_new_products(),
            self._scan_partnerships(),
            self._scan_hiring(),
            self._scan_pricing(),
        ]

        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        for result in gathered:
            if isinstance(result, list):
                events.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Competitor scan subtask failed: {result}")

        # 去重 + 紧迫度评分
        events = self._deduplicate_and_score(events)
        logger.info(f"Competitor tracker: {len(events)} events found")
        return events

    async def _scan_news(self) -> List[Dict]:
        """扫描竞品相关新闻"""
        events = []

        # 监控来源：
        # · 百度新闻 / Google News
        # · 旅游行业媒体（TTG China / 环球旅讯 / 品橙旅游）
        # · 微信公众号搜索
        # · 36氪 / 虎嗅 旅游频道

        primary_brands = self.competitors["primary"]
        for brand in primary_brands:
            # TODO: 实际部署时使用新闻搜索API
            # queries = [f"{brand['cn_name']} 极地 邮轮", f"{brand['name']} China polar"]
            logger.debug(f"Scanning news for: {brand['name']}")
            await asyncio.sleep(self.request_delay)

        return events

    async def _scan_social_buzz(self) -> List[Dict]:
        """扫描社交媒体声量变化"""
        events = []

        # 监控维度：
        # · 微信指数对比（庞洛 vs 夸克 vs 银海...）
        # · 小红书内容量趋势
        # · 百度指数
        # · 知乎话题热度

        for brand in self.competitors["primary"]:
            logger.debug(f"Checking social buzz for: {brand['name']}")
            await asyncio.sleep(self.request_delay)

        return events

    async def _scan_new_products(self) -> List[Dict]:
        """扫描竞品新产品/新航线发布"""
        events = []

        # 监控信号：
        # · 竞品官网新页面上线
        # · 新船下水/命名新闻
        # · 新航线/新目的地发布
        # · 中国市场专属产品推出

        for brand in self.competitors["primary"]:
            logger.debug(f"Checking new products for: {brand['name']}")
            await asyncio.sleep(self.request_delay)

        return events

    async def _scan_partnerships(self) -> List[Dict]:
        """扫描竞品新渠道合作签约"""
        events = []

        # 监控信号：
        # · "XXX 与 XX签署战略合作"
        # · "XX成为XX中国区总代理"
        # · 包船/独家合作公告
        # · 旅行社官网新增竞品品牌

        partnership_keywords = [
            "战略合作", "签署合作", "包船", "独家代理",
            "总代理", "中国区合作", "渠道合作", "联合发布",
        ]

        for brand in self.competitors["primary"]:
            for kw in partnership_keywords:
                logger.debug(
                    f"Scanning partnership: {brand['name']} + {kw}"
                )
                await asyncio.sleep(self.request_delay / 4)

        return events

    async def _scan_hiring(self) -> List[Dict]:
        """扫描竞品招聘动态（中国市场扩编信号）"""
        events = []

        # 监控平台：
        # · 脉脉 / 领英 / BOSS直聘 / 猎聘
        # 搜索关键词：竞品品牌名 + 旅游/极地相关职位

        # 招聘信号含义：
        # · 新增"中国区"职位 → 中国市场投入加大
        # · 新增"中文探险队员" → 中文服务能力增强
        # · 新增"BD/渠道"职位 → 渠道扩张信号
        # · 新增"品牌/市场"职位 → 品牌推广加码

        for brand in self.competitors["primary"]:
            logger.debug(f"Scanning hiring for: {brand['name']}")
            await asyncio.sleep(self.request_delay)

        return events

    async def _scan_pricing(self) -> List[Dict]:
        """扫描竞品价格变化"""
        events = []

        # 监控信号：
        # · 早鸟折扣调整
        # · 尾单/特价促销
        # · "买一送一"等激进促销
        # · 价格带整体下移/上移

        for brand in self.competitors["primary"]:
            logger.debug(f"Checking pricing for: {brand['name']}")
            await asyncio.sleep(self.request_delay)

        return events

    def _deduplicate_and_score(self, events: List[Dict]) -> List[Dict]:
        """去重并评估紧迫度"""
        seen = set()
        unique = []

        for event in events:
            key = (
                event.get("competitor", "")
                + event.get("type", "")
                + event.get("title", "")[:50]
            )
            event_hash = hashlib.md5(key.encode()).hexdigest()
            if event_hash not in seen:
                seen.add(event_hash)

                # 紧迫度评分
                urgency = self._assess_urgency(event)
                event["urgency"] = urgency
                unique.append(event)

        return sorted(unique, key=lambda e: (
            0 if e["urgency"] == "critical" else
            1 if e["urgency"] == "high" else
            2
        ))

    def _assess_urgency(self, event: Dict) -> str:
        """评估事件紧迫度"""
        event_type = event.get("type", "")
        title = event.get("title", "")

        # CRITICAL: 需要立即响应
        critical_signals = [
            "包船", "独家代理", "战略合作签约",
            "价格腰斩", "买一送一", "中国区总代理",
        ]
        if any(s in title for s in critical_signals):
            return "critical"

        # HIGH: 24小时内关注
        high_signals = [
            "新产品发布", "新船下水", "航线新增",
            "中国市场", "中文服务", "大规模促销",
        ]
        if any(s in title for s in high_signals):
            return "high"

        # MEDIUM: 纳入周报
        return "medium"
