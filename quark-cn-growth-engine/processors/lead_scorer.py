"""
线索评分引擎
基于多维度信号对渠道合作伙伴线索进行自动评分和排序
"""
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger("quark.processors.lead_scorer")


class LeadScorer:
    """
    多维线索评分模型

    评分维度（总分100）：
    1. 资质认证 (50分)：IAATO/AECO成员身份
    2. 业务规模 (25分)：年极地客量、产品线数量
    3. 品牌契合度 (15分)：是否提及Quark、专业匹配度
    4. 活跃信号 (10分)：近期动态、招聘、内容更新
    """

    def __init__(self, config: dict, dedup_engine=None):
        self.config = config
        self.scoring_weights = config["nlp"]["lead_scoring"]["weights"]
        self.thresholds = config["nlp"]["lead_scoring"]["thresholds"]
        self.dedup = dedup_engine

        # 已知IAATO/AECO成员名单（自动加分）
        self.iaato_members = self._load_iaato_members()
        self.aeco_members = self._load_aeco_members()

    def _load_iaato_members(self) -> set:
        """加载已知IAATO中国成员"""
        # 基于IAATO官网公开信息
        return {
            "极至旅行", "3Polar", "极之美", "tripolers",
            "北京船客国际旅行社", "众信旅游集团", "UTour Group",
        }

    def _load_aeco_members(self) -> set:
        """加载已知AECO中国成员"""
        return {
            "极至旅行", "3Polar", "极之美", "tripolers",
            "北京船客国际旅行社", "众信旅游集团", "UTour Group",
        }

    async def score_batch(self, leads: List[Dict]) -> List[Dict]:
        """批量评分"""
        scored = []
        for lead in leads:
            try:
                scored_lead = await self.score_single(lead)
                scored.append(scored_lead)
            except Exception as e:
                logger.error(f"Failed to score lead {lead.get('id')}: {e}")
                lead["score"] = 0
                lead["score_breakdown"] = {"error": str(e)}
                scored.append(lead)
        return scored

    async def score_single(self, lead: Dict) -> Dict:
        """对单条线索进行评分"""
        breakdown = {}

        # 1. 资质认证 (50分)
        certification_score = self._score_certifications(lead)
        breakdown["certifications"] = certification_score

        # 2. 业务规模 (25分)
        scale_score = self._score_business_scale(lead)
        breakdown["business_scale"] = scale_score

        # 3. 品牌契合度 (15分)
        fit_score = self._score_brand_fit(lead)
        breakdown["brand_fit"] = fit_score

        # 4. 活跃信号 (10分)
        activity_score = self._score_activity_signals(lead)
        breakdown["activity"] = activity_score

        total_score = certification_score + scale_score + fit_score + activity_score
        lead["score"] = min(total_score, 100)
        lead["score_breakdown"] = breakdown
        lead["tier"] = self._score_to_tier(lead["score"])
        lead["scored_at"] = datetime.now().isoformat()

        return lead

    def _score_certifications(self, lead: Dict) -> int:
        """
        资质认证评分

        IAATO正式成员: +30
        AECO正式成员:  +20
        双认证额外加分:  +5 (叠加)
        总计最大: 55 → 归一化到50
        """
        score = 0
        company_names = lead.get("extracted_companies", [])
        lead_name = lead.get("company_name", "")
        all_names = list(company_names) + [lead_name]

        has_iaato = any(
            name in self.iaato_members for name in all_names
        )
        has_aeco = any(
            name in self.aeco_members for name in all_names
        )

        if has_iaato:
            score += self.scoring_weights["is_iaato_member"]
        if has_aeco:
            score += self.scoring_weights["is_aeco_member"]

        # 双认证额外加分
        if has_iaato and has_aeco:
            score += 5

        return min(score, 50)

    def _score_business_scale(self, lead: Dict) -> int:
        """
        业务规模评分

        极地产品线数量:
        - 5条以上:  +10
        - 2-4条:    +5
        - 有南极:    +3
        - 有北极:    +3

        年极地客量:
        - >1000人:   +10
        - 500-1000:  +7
        - 100-500:   +4
        - <100:      +2

        最大: 20 → 归一化到25
        """
        score = 0
        text = lead.get("raw_text", "").lower()

        # 产品线检测
        polar_terms = {
            "南极半岛": 1, "南极三岛": 1, "南极点": 1,
            "南极圈": 1, "北极点": 1, "斯瓦尔巴": 1,
            "格陵兰": 1, "冰岛": 1, "罗斯海": 1,
        }
        product_count = sum(1 for term in polar_terms if term in text)
        if product_count >= 5:
            score += 10
        elif product_count >= 2:
            score += 5
        if "南极" in text:
            score += 3
        if "北极" in text:
            score += 3

        # 客量检测（从文本中提取）
        volume_match = re.search(r"年(?:极地|南极|南北极).{0,10}(\d{3,5})\s*(?:人|名|位|游客)", text)
        if volume_match:
            volume = int(volume_match.group(1))
            if volume > 1000:
                score += 10
            elif volume > 500:
                score += 7
            elif volume > 100:
                score += 4
            else:
                score += 2

        return min(score, 25)

    def _score_brand_fit(self, lead: Dict) -> int:
        """
        品牌契合度评分

        - 提及Quark/夸克: +8
        - 高端/定制/奢华定位: +4
        - 探险/专业/科考关键词: +3
        """
        score = 0
        text = lead.get("raw_text", "").lower()

        # Quark提及
        quark_keywords = ["quark", "夸克", "夸克探险", "quark expeditions"]
        if any(kw in text for kw in quark_keywords):
            score += 8

        # 高端定位
        premium_keywords = ["高端", "奢华", "定制", "私人", "专属", "尊享", "VIP"]
        if any(kw in text for kw in premium_keywords):
            score += 4

        # 探险/专业
        adventure_keywords = ["探险", "科考", "专业", "深度", "极地专家", "探险队"]
        if any(kw in text for kw in adventure_keywords):
            score += 3

        return min(score, 15)

    def _score_activity_signals(self, lead: Dict) -> int:
        """
        活跃信号评分

        - 近期有产品更新/招聘: +5
        - 社交媒体活跃: +3
        - 有内容/文章发布: +2
        """
        score = 0
        text = lead.get("raw_text", "")

        activity_keywords = ["招聘", "新航线", "新品发布", "最新", "2025", "2026"]
        if any(kw in text for kw in activity_keywords):
            score += 5

        social_keywords = ["小红书", "公众号", "抖音", "视频号", "直播"]
        if any(kw in text for kw in social_keywords):
            score += 3

        content_keywords = ["攻略", "文章", "测评", "游记", "干货"]
        if any(kw in text for kw in content_keywords):
            score += 2

        return min(score, 10)

    def _score_to_tier(self, score: int) -> str:
        """评分转等级"""
        if score >= self.thresholds["hot"]:
            return "hot"
        elif score >= self.thresholds["warm"]:
            return "warm"
        return "cold"

    async def refresh_all(self) -> int:
        """刷新所有未跟进线索的评分（有新数据时触发）"""
        # TODO: 从数据库读取所有 status='new'/'open' 的线索重新评分
        logger.info("Refreshing all lead scores...")
        return 0
