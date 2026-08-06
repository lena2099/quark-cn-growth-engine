"""
Quark CN Growth Engine — 总调度器
负责所有定时任务的注册、调度和监控
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from collectors.channel_discovery import ChannelDiscoveryCollector
from collectors.social_listener import SocialListener
from collectors.competitor_tracker import CompetitorTracker
from collectors.industry_radar import IndustryRadar
from processors.lead_scorer import LeadScorer
from processors.dedup import DedupEngine
from outreach.linkedin_connector import LinkedInConnector
from outreach.maimai_connector import MaimaiConnector
from content.distribution import ContentDistributor
from dashboard.alerts import AlertEngine
from utils.config import load_config
from utils.db import init_db, get_db_session
from utils.logging_config import setup_logging

logger = logging.getLogger("quark.scheduler")


class QuarkGrowthEngine:
    """Quark CN Growth Engine 主控制器"""

    def __init__(self, config_path: str = None):
        self.config = load_config(config_path)
        self.scheduler = AsyncIOScheduler(
            timezone=self.config["scheduler"]["timezone"]
        )
        self.running = False

        # 组件延迟初始化
        self.channel_discovery = None
        self.social_listener = None
        self.competitor_tracker = None
        self.industry_radar = None
        self.lead_scorer = None
        self.dedup = None
        self.linkedin = None
        self.maimai = None
        self.content_distributor = None
        self.alert_engine = None

    async def initialize(self):
        """初始化所有子系统"""
        logger.info("Initializing Quark CN Growth Engine...")

        await init_db(self.config["database"])

        self.channel_discovery = ChannelDiscoveryCollector(self.config)
        self.social_listener = SocialListener(self.config)
        self.competitor_tracker = CompetitorTracker(self.config)
        self.industry_radar = IndustryRadar(self.config)
        self.dedup = DedupEngine()
        self.lead_scorer = LeadScorer(self.config, self.dedup)
        self.linkedin = LinkedInConnector(self.config)
        self.maimai = MaimaiConnector(self.config)
        self.content_distributor = ContentDistributor(self.config)
        self.alert_engine = AlertEngine(self.config)

        logger.info("All subsystems initialized.")

    def register_jobs(self):
        """注册所有定时任务"""
        sc = self.config["scheduler"]["jobs"]

        # ── 采集任务 ──
        self.scheduler.add_job(
            self._run_channel_discovery,
            CronTrigger.from_crontab(sc["channel_discovery"]["cron"]),
            id="channel_discovery",
            name="渠道伙伴发现引擎",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._run_linkedin_scan,
            CronTrigger.from_crontab(sc["linkedin_scan"]["cron"]),
            id="linkedin_scan",
            name="领英联系人自动采集",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._run_competitor_monitor,
            CronTrigger.from_crontab(sc["competitor_monitor"]["cron"]),
            id="competitor_monitor",
            name="竞品动态监控",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._run_industry_radar,
            CronTrigger.from_crontab(sc["industry_radar"]["cron"]),
            id="industry_radar",
            name="行业趋势雷达",
            replace_existing=True,
        )

        # ── 处理任务 ──
        self.scheduler.add_job(
            self._run_lead_scoring,
            CronTrigger.from_crontab("0 */2 * * *"),  # 每2小时
            id="lead_scoring",
            name="线索评分",
            replace_existing=True,
        )

        # ── 触达任务 ──
        self.scheduler.add_job(
            self._run_content_distribution,
            CronTrigger.from_crontab(sc["content_distribution"]["cron"]),
            id="content_distribution",
            name="内容分发",
            replace_existing=True,
        )

        # ── 报告任务 ──
        self.scheduler.add_job(
            self._generate_daily_report,
            CronTrigger.from_crontab(sc["lead_report_generation"]["cron"]),
            id="daily_report",
            name="线索日报生成",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._generate_weekly_report,
            CronTrigger.from_crontab(sc["weekly_report"]["cron"]),
            id="weekly_report",
            name="周报生成",
            replace_existing=True,
        )

        # ── 健康检查 ──
        self.scheduler.add_job(
            self._health_check,
            CronTrigger.from_crontab("0 * * * *"),  # 每小时
            id="health_check",
            name="系统健康检查",
            replace_existing=True,
        )

        logger.info(f"Registered {len(self.scheduler.get_jobs())} scheduled jobs.")

    # ═══════════════════════════════════════════════════════════════
    # 任务执行方法
    # ═══════════════════════════════════════════════════════════════

    async def _run_channel_discovery(self):
        """工作流1：渠道合作伙伴发现引擎"""
        logger.info("Starting channel discovery...")
        try:
            leads = await self.channel_discovery.scan()
            logger.info(f"Channel discovery found {len(leads)} raw leads.")

            new_leads = await self.dedup.filter_new(leads)
            if new_leads:
                scored = await self.lead_scorer.score_batch(new_leads)
                await self._store_leads(scored)

                hot_leads = [l for l in scored if l["score"] >= 70]
                if hot_leads:
                    await self.alert_engine.push_hot_leads(hot_leads)

            logger.info(
                f"Channel discovery complete: {len(new_leads)} new, "
                f"{len([l for l in (new_leads or [])])} hot leads"
            )
        except Exception as e:
            logger.error(f"Channel discovery failed: {e}", exc_info=True)

    async def _run_linkedin_scan(self):
        """工作流2：领英/脉脉联系人采集"""
        logger.info("Starting LinkedIn/Maimai contact scan...")
        try:
            linkedin_results = await self.linkedin.scan_targets()
            maimai_results = await self.maimai.scan_targets()

            all_contacts = linkedin_results + maimai_results
            new_contacts = await self.dedup.filter_new_contacts(all_contacts)
            await self._store_contacts(new_contacts)

            logger.info(
                f"Contact scan complete: LI={len(linkedin_results)}, "
                f"MM={len(maimai_results)}, New={len(new_contacts)}"
            )
        except Exception as e:
            logger.error(f"Contact scan failed: {e}", exc_info=True)

    async def _run_competitor_monitor(self):
        """工作流3：竞品动态监控"""
        logger.info("Starting competitor monitoring...")
        try:
            events = await self.competitor_tracker.scan()
            if events:
                urgent = [e for e in events if e.get("urgency") in ("high", "critical")]
                if urgent:
                    await self.alert_engine.push_competitor_alerts(urgent)
                await self._store_competitor_events(events)
            logger.info(f"Competitor monitor complete: {len(events)} events found.")
        except Exception as e:
            logger.error(f"Competitor monitor failed: {e}", exc_info=True)

    async def _run_industry_radar(self):
        """工作流4：行业趋势/机会雷达"""
        logger.info("Starting industry radar...")
        try:
            signals = await self.industry_radar.scan()
            if signals:
                await self._store_signals(signals)
                await self.alert_engine.push_daily_signals(signals)
            logger.info(f"Industry radar complete: {len(signals)} signals.")
        except Exception as e:
            logger.error(f"Industry radar failed: {e}", exc_info=True)

    async def _run_lead_scoring(self):
        """线索评分更新"""
        logger.info("Updating lead scores...")
        try:
            updated = await self.lead_scorer.refresh_all()
            logger.info(f"Lead scoring complete: {updated} leads updated.")
        except Exception as e:
            logger.error(f"Lead scoring failed: {e}", exc_info=True)

    async def _run_content_distribution(self):
        """工作流5：内容分发"""
        logger.info("Starting content distribution...")
        try:
            result = await self.content_distributor.distribute()
            logger.info(f"Content distribution complete: {result}")
        except Exception as e:
            logger.error(f"Content distribution failed: {e}", exc_info=True)

    async def _generate_daily_report(self):
        """每日线索摘要报告"""
        logger.info("Generating daily report...")
        try:
            async with get_db_session() as db:
                report = await db.generate_daily_report()
                await self.alert_engine.push_daily_digest(report)
        except Exception as e:
            logger.error(f"Daily report generation failed: {e}", exc_info=True)

    async def _generate_weekly_report(self):
        """每周综合报告"""
        logger.info("Generating weekly report...")
        try:
            async with get_db_session() as db:
                report = await db.generate_weekly_report()
                await self.alert_engine.push_weekly_report(report)
        except Exception as e:
            logger.error(f"Weekly report generation failed: {e}", exc_info=True)

    async def _health_check(self):
        """系统健康检查"""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "scheduler_running": self.scheduler.running,
                "job_count": len(self.scheduler.get_jobs()),
            }
            logger.debug(f"Health check: {status}")
        except Exception as e:
            logger.error(f"Health check failed: {e}")

    # ═══════════════════════════════════════════════════════════════
    # 数据持久化
    # ═══════════════════════════════════════════════════════════════

    async def _store_leads(self, leads):
        """存储渠道线索"""
        async with get_db_session() as db:
            await db.bulk_insert_leads(leads)

    async def _store_contacts(self, contacts):
        """存储联系人"""
        async with get_db_session() as db:
            await db.bulk_insert_contacts(contacts)

    async def _store_competitor_events(self, events):
        """存储竞品动态"""
        async with get_db_session() as db:
            await db.bulk_insert_competitor_events(events)

    async def _store_signals(self, signals):
        """存储行业信号"""
        async with get_db_session() as db:
            await db.bulk_insert_signals(signals)

    # ═══════════════════════════════════════════════════════════════
    # 生命周期
    # ═══════════════════════════════════════════════════════════════

    async def start(self):
        """启动引擎"""
        await self.initialize()
        self.register_jobs()
        self.scheduler.start()
        self.running = True
        logger.info("=" * 60)
        logger.info("Quark CN Growth Engine is RUNNING")
        logger.info(f"Timezone: {self.config['scheduler']['timezone']}")
        logger.info(f"Jobs: {len(self.scheduler.get_jobs())}")
        logger.info("=" * 60)

    async def stop(self):
        """优雅停机"""
        logger.info("Shutting down Quark CN Growth Engine...")
        self.running = False
        self.scheduler.shutdown(wait=True)
        logger.info("Engine stopped.")


# ── 入口 ────────────────────────────────────────────────
async def main():
    setup_logging()
    engine = QuarkGrowthEngine()

    # 信号处理
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(engine.stop()))

    await engine.start()

    # 保持运行
    try:
        while engine.running:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())
