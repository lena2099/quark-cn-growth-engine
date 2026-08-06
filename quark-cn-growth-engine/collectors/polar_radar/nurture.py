"""
客户培育引擎 (Nurture Engine)

核心策略：
  不是"发现需求→卖"，而是"发现需求→教育→社群→转化"

培育路径：
  Discovery → Educate → Engage → Convert
   (发现)     (教育)      (社群)    (转化)

每个阶段有对应的内容策略和触达方式。
"""
import hashlib
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger("quark.processors.nurture")


class NurtureStage(Enum):
    DISCOVERY = "discovery"    # 发现 — 持续观察
    EDUCATE = "educate"        # 教育 — 内容培育
    ENGAGE = "engage"          # 社群 — 加入社群/参加活动
    CONVERT = "convert"        # 转化 — 销售1对1
    LOYAL = "loyal"            # 忠诚 — 老客推荐/复购


# ═══════════════════════════════════════════════════════
# 内容库
# ═══════════════════════════════════════════════════════

CONTENT_LIBRARY = {
    # ── 梦想制造 (Discovery → Educate) ──
    "dream_video_1": {
        "id": "dream_video_1",
        "title": "如果人生只去一次极地，你选择南极还是北极？",
        "type": "video",
        "duration": "3min",
        "platform": ["douyin", "shipinhao"],
        "stage": [NurtureStage.DISCOVERY, NurtureStage.EDUCATE],
        "goal": "唤醒极地认知",
        "url_template": "/content/dream-polar-choice.mp4",
    },
    "dream_video_2": {
        "id": "dream_video_2",
        "title": "企业家50岁以后，应该给自己一次南极",
        "type": "video",
        "duration": "2min",
        "platform": ["douyin", "shipinhao"],
        "stage": [NurtureStage.DISCOVERY],
        "goal": "身份认同+极地联想",
        "url_template": "/content/entrepreneur-antarctic.mp4",
    },
    "dream_video_3": {
        "id": "dream_video_3",
        "title": "世界最后一块大陆到底长什么样？",
        "type": "video",
        "duration": "5min",
        "platform": ["douyin", "shipinhao", "xiaohongshu"],
        "stage": [NurtureStage.DISCOVERY, NurtureStage.EDUCATE],
        "goal": "极地视觉震撼",
        "url_template": "/content/last-continent.mp4",
    },
    "dream_article_1": {
        "id": "dream_article_1",
        "title": "去一次南极到底要花多少钱？2026最新价格拆解",
        "type": "article",
        "platform": ["wechat", "xiaohongshu", "zhihu"],
        "stage": [NurtureStage.DISCOVERY, NurtureStage.EDUCATE],
        "goal": "价格透明化，建立信任",
        "url_template": "/content/antarctic-cost-breakdown-2026.html",
    },
    "dream_article_2": {
        "id": "dream_article_2",
        "title": "中国南极游客突破1万人：为什么越来越多中国人选择去南极？",
        "type": "article",
        "platform": ["wechat", "zhihu"],
        "stage": [NurtureStage.DISCOVERY],
        "goal": "社会证明+趋势认同",
        "url_template": "/content/china-antarctic-trend.html",
    },

    # ── 价值教育 (Educate) ──
    "educate_guide_1": {
        "id": "educate_guide_1",
        "title": "《第一次南极旅行指南》",
        "type": "ebook",
        "pages": 24,
        "platform": ["wechat", "wecom"],
        "stage": [NurtureStage.EDUCATE],
        "goal": "领英入口，获取企业微信联系人",
        "url_template": "/content/first-antarctic-guide.pdf",
        "gated": True,  # 需要留资
    },
    "educate_compare": {
        "id": "educate_compare",
        "title": "南极邮轮怎么选？庞洛 vs 夸克 vs 银海 vs A21 全对比",
        "type": "article",
        "platform": ["wechat", "xiaohongshu", "zhihu"],
        "stage": [NurtureStage.EDUCATE],
        "goal": "建立品类认知，突出Quark差异化",
        "url_template": "/content/polar-cruise-comparison.html",
    },
    "educate_helicopter": {
        "id": "educate_helicopter",
        "title": "Ultramarine号：全球唯一配备双直升机的极地探险船",
        "type": "video",
        "duration": "4min",
        "platform": ["douyin", "shipinhao", "xiaohongshu"],
        "stage": [NurtureStage.EDUCATE],
        "goal": "USP强化记忆",
        "url_template": "/content/ultramarine-helicopter.mp4",
    },
    "educate_faq_100": {
        "id": "educate_faq_100",
        "title": "《极地旅行100问》",
        "type": "ebook",
        "pages": 56,
        "platform": ["wechat", "wecom"],
        "stage": [NurtureStage.EDUCATE],
        "goal": "深度教育+信任建立",
        "url_template": "/content/polar-travel-100-faq.pdf",
        "gated": True,
    },

    # ── 社群转化 (Engage) ──
    "engage_sharing": {
        "id": "engage_sharing",
        "title": "线上分享会：南极探险队长带你云游极地",
        "type": "event",
        "platform": ["wecom", "zoom"],
        "stage": [NurtureStage.ENGAGE],
        "goal": "社群归属感+真人连接",
        "frequency": "每月1次",
    },
    "engage_customer_story": {
        "id": "engage_customer_story",
        "title": "真实客户故事：50岁企业家的南极之旅",
        "type": "article",
        "platform": ["wechat", "wecom_group"],
        "stage": [NurtureStage.ENGAGE],
        "goal": "身份认同+社会证明",
        "url_template": "/content/entrepreneur-antarctic-story.html",
    },
    "engage_photo_contest": {
        "id": "engage_photo_contest",
        "title": "Quark极地摄影大赛",
        "type": "event",
        "platform": ["wechat", "xiaohongshu"],
        "stage": [NurtureStage.ENGAGE],
        "goal": "UGC+社群激活",
        "frequency": "每年1次",
    },

    # ── 销售转化 (Convert) ──
    "convert_catalog": {
        "id": "convert_catalog",
        "title": "《2026-2027南极季航线手册》",
        "type": "catalog",
        "pages": 32,
        "platform": ["wecom", "email"],
        "stage": [NurtureStage.CONVERT],
        "goal": "产品选择+价格锚定",
        "url_template": "/content/2026-2027-catalog.pdf",
    },
    "convert_deck": {
        "id": "convert_deck",
        "title": "Quark探险对比优势一览（销售专用）",
        "type": "deck",
        "platform": ["wecom"],
        "stage": [NurtureStage.CONVERT],
        "goal": "竞品对比+决策推进",
        "url_template": "/content/quark-vs-competitors.pdf",
    },
    "convert_early_bird": {
        "id": "convert_early_bird",
        "title": "早鸟限定：前50名预订赠直升机冰原体验",
        "type": "promotion",
        "platform": ["wecom"],
        "stage": [NurtureStage.CONVERT],
        "goal": "紧迫感+稀缺感",
    },

    # ── 老客忠诚 (Loyal) ──
    "loyal_referral": {
        "id": "loyal_referral",
        "title": "推荐有礼：推荐好友各得¥5000抵扣券",
        "type": "promotion",
        "platform": ["wecom", "wechat"],
        "stage": [NurtureStage.LOYAL],
        "goal": "老客推荐新客",
    },
    "loyal_arctic": {
        "id": "loyal_arctic",
        "title": "南极归来，下一站：北极格陵兰",
        "type": "article",
        "platform": ["wecom", "wechat", "email"],
        "stage": [NurtureStage.LOYAL],
        "goal": "北极复购触达",
        "url_template": "/content/from-antarctic-to-arctic.html",
    },
}


# ═══════════════════════════════════════════════════════
# 培育引擎
# ═══════════════════════════════════════════════════════

class NurtureEngine:
    """根据用户画像和评分，自动推荐内容和触达策略"""

    def __init__(self):
        self.content_lib = CONTENT_LIBRARY

    def get_journey(self, lead: Dict) -> Dict:
        """
        为单个线索生成培育旅程

        输入：PolarLead 数据（或字典）
        输出：包含阶段、内容推荐、触达计划的旅程对象
        """
        score = lead.get("score", 0)
        stage = self._determine_stage(score)

        return {
            "lead_id": lead.get("id", ""),
            "current_stage": stage.value,
            "score": score,
            "content_sequence": self._recommend_sequence(lead, stage),
            "touchpoint_schedule": self._build_schedule(lead, stage),
            "wecom_tags": self._generate_wecom_tags(lead),
            "sales_talking_points": self._generate_talking_points(lead),
        }

    def _determine_stage(self, score: float) -> NurtureStage:
        if score >= 70:
            return NurtureStage.CONVERT
        elif score >= 40:
            return NurtureStage.ENGAGE
        elif score >= 20:
            return NurtureStage.EDUCATE
        return NurtureStage.DISCOVERY

    def _recommend_sequence(self, lead: Dict, stage: NurtureStage) -> List[Dict]:
        """按阶段推荐内容序列"""
        # Stage → 推荐内容顺序
        stage_content_map = {
            NurtureStage.DISCOVERY: [
                "dream_video_1", "dream_video_3", "dream_article_1",
            ],
            NurtureStage.EDUCATE: [
                "educate_guide_1",    # 引导留资
                "educate_compare",    # 品类教育
                "educate_helicopter", # USP强化
                "dream_article_1",    # 价格透明
            ],
            NurtureStage.ENGAGE: [
                "educate_faq_100",     # 深度内容
                "engage_sharing",      # 线上分享会
                "engage_customer_story", # 客户故事
                "educate_compare",     # 反复教育
            ],
            NurtureStage.CONVERT: [
                "convert_catalog",     # 航线手册
                "convert_deck",        # 竞品对比
                "convert_early_bird",  # 早鸟激励
                "engage_sharing",      # 最后一场分享会
            ],
            NurtureStage.LOYAL: [
                "loyal_referral",      # 推荐激励
                "loyal_arctic",        # 北极复购
                "engage_photo_contest",# 摄影大赛
            ],
        }

        content_ids = stage_content_map.get(stage, [])
        result = []
        for cid in content_ids:
            if cid in self.content_lib:
                result.append(self.content_lib[cid])
        return result

    def _build_schedule(self, lead: Dict, stage: NurtureStage) -> List[Dict]:
        """构建触达时间表"""
        now = datetime.now()

        schedules = {
            NurtureStage.DISCOVERY: [
                {"day": 0, "action": "加入观察列表", "channel": "system"},
                {"day": 1, "action": "推送梦想视频", "channel": "douyin/shipinhao"},
                {"day": 3, "action": "推送价格透明文章", "channel": "xiaohongshu/wechat"},
                {"day": 7, "action": "检查信号变化，决定是否升级", "channel": "system"},
            ],
            NurtureStage.EDUCATE: [
                {"day": 0, "action": "推送《第一次南极旅行指南》(留资)", "channel": "wechat"},
                {"day": 2, "action": "推送邮轮对比文章", "channel": "wechat"},
                {"day": 4, "action": "推送Ultramarine直升机视频", "channel": "shipinhao"},
                {"day": 7, "action": "推送《极地旅行100问》", "channel": "wecom"},
                {"day": 14, "action": "邀请参加线上分享会", "channel": "wecom"},
            ],
            NurtureStage.ENGAGE: [
                {"day": 0, "action": "拉入「极地探索」企业微信社群", "channel": "wecom"},
                {"day": 1, "action": "发送社群欢迎+自我介绍引导", "channel": "wecom_group"},
                {"day": 3, "action": "分享客户真实故事", "channel": "wecom_group"},
                {"day": 7, "action": "线上分享会提醒", "channel": "wecom"},
                {"day": 8, "action": "分享会后的1对1跟进", "channel": "wecom_dm"},
                {"day": 14, "action": "判断转化意向，决定是否升级", "channel": "system"},
            ],
            NurtureStage.CONVERT: [
                {"day": 0, "action": "分配专属销售顾问", "channel": "system"},
                {"day": 0, "action": "发送《航线手册》+ 个性化推荐", "channel": "wecom_dm"},
                {"day": 1, "action": "1对1电话/视频沟通", "channel": "phone"},
                {"day": 3, "action": "发送竞品对比优势表", "channel": "wecom_dm"},
                {"day": 5, "action": "早鸟优惠提醒", "channel": "wecom_dm"},
                {"day": 7, "action": "最后跟进：锁定舱位", "channel": "phone"},
                {"day": 14, "action": "未成交→降级到Engage继续培育", "channel": "system"},
            ],
        }

        base = schedules.get(stage, [])
        return [
            {
                **item,
                "scheduled_date": (now + timedelta(days=item["day"])).strftime("%Y-%m-%d"),
            }
            for item in base
        ]

    def _generate_wecom_tags(self, lead: Dict) -> List[str]:
        """生成企业微信客户标签"""
        tags = []

        # 阶段标签
        stage = self._determine_stage(lead.get("score", 0))
        stage_tags = {
            NurtureStage.DISCOVERY: "南极兴趣-观察",
            NurtureStage.EDUCATE: "南极兴趣-培育中",
            NurtureStage.ENGAGE: "南极兴趣-高意向",
            NurtureStage.CONVERT: "南极-待成交",
            NurtureStage.LOYAL: "南极-老客",
        }
        tags.append(stage_tags.get(stage, "未分类"))

        # 画像标签
        if lead.get("age_range"):
            tags.append(f"年龄-{lead['age_range']}")
        if lead.get("profession_category"):
            tags.append(f"职业-{lead['profession_category']}")
        if lead.get("travel_level"):
            tags.append(f"旅行-{lead['travel_level']}")
        if lead.get("estimated_budget"):
            tags.append(f"预算-{lead['estimated_budget']}")

        # 来源标签
        tags.append(f"来源-{lead.get('source', '未知')}")

        return tags

    def _generate_talking_points(self, lead: Dict) -> List[str]:
        """生成销售话术要点"""
        points = []
        score = lead.get("score", 0)
        profession = lead.get("profession_category", "")
        age = lead.get("age_range", "")
        travel = lead.get("travel_level", "")
        has_polar = lead.get("has_polar_awareness", False)
        budget = lead.get("estimated_budget", "")

        # 基于画像的话术锚点
        if profession == "企业主":
            points.append("💼 您是企业家，我特别推荐Ultramarine号的直升机体验——时间和体验对您来说比价格重要，直升机能带您到常规船去不了的冰原深处，这才是真正的'独家体验'")
        elif profession == "企业高管":
            points.append("💼 您这样经常出差的高管，最需要的就是纯粹的安静。南极没有信号、没有打扰，是最极致的'数字排毒'。Quark的探险队规模是业内最大的，安全性和专业度最有保障")
        elif profession == "专业人士":
            points.append("🎓 您作为专业人士，肯定会欣赏Quark 30年只做极地的专注。我们的探险队员里有冰川学家、海洋生物学家、极地历史学家，科考深度远超其他船公司")

        if travel == "骨灰级":
            points.append("🌍 您已经走过这么多国家了，南极一定不能将就。普通路线您会觉得太浅，Quark有罗斯海、威德尔海、南极点这些真正硬核的线路")
        elif age == "55+":
            points.append("🎯 这个年纪去南极，要的不是打卡，是一份值得回忆终身的体验。Quark的探险队员会在登陆时陪你慢慢走，确保安全和深度体验兼具")

        if has_polar:
            points.append(f"📚 您对极地已经有了解了，我直接给您看最核心的：{budget}预算内，这几条航线最适合您——")
        else:
            points.append("🐧 您可能想知道——去南极到底是什么感觉？我给您发一段我们客户实拍的视频，3分钟就能感受到")

        # 竞品防御
        points.append("🛡️ 市面上庞洛偏重奢华酒店体验，A21主打飞越德雷克海峡。Quark是唯一把'探险深度'做到极致的——更多的登陆次数、更专业的探险队、还有独一无二的直升机。这不是最贵的船，但是最'值'的船")

        return points


# ═══════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════

def demo_nurture():
    """演示培育引擎"""
    engine = NurtureEngine()

    test_leads = [
        {
            "id": "wang_001",
            "score": 60,
            "age_range": "45-55",
            "profession_category": "企业主",
            "travel_level": "中度",
            "estimated_budget": "20-30万",
            "has_polar_awareness": True,
            "source": "xiaohongshu",
            "raw_text": "50岁了，把公司交给职业经理人...",
        },
        {
            "id": "linda_002",
            "score": 55,
            "age_range": "35-44",
            "profession_category": "企业高管",
            "travel_level": "骨灰级",
            "estimated_budget": "30万+",
            "has_polar_awareness": False,
            "source": "xiaohongshu",
            "raw_text": "今年已经飞了80段了，头等舱坐到麻木...",
        },
        {
            "id": "photographer_003",
            "score": 48,
            "age_range": "",
            "profession_category": "",
            "travel_level": "重度",
            "estimated_budget": "10-20万",
            "has_polar_awareness": True,
            "source": "xiaohongshu",
            "raw_text": "求推荐能拍到帝企鹅的南极线路...",
        },
    ]

    for lead in test_leads:
        journey = engine.get_journey(lead)
        print(f"\n{'='*60}")
        print(f"🎯 {lead['id']} | 评分: {lead['score']} | 阶段: {journey['current_stage']}")
        print(f"{'='*60}")

        print("\n📊 企业微信标签:")
        for tag in journey["wecom_tags"]:
            print(f"   #{tag}")

        print("\n📚 推荐内容序列:")
        for i, content in enumerate(journey["content_sequence"], 1):
            print(f"   {i}. [{content['type']}] {content['title']}")

        print("\n📅 触达计划:")
        for item in journey["touchpoint_schedule"][:5]:
            print(f"   Day {item['day']:2d} ({item['scheduled_date']}) | {item['channel']:12s} | {item['action']}")

        print("\n💬 销售话术:")
        for point in journey["sales_talking_points"]:
            print(f"   {point[:100]}...")


if __name__ == "__main__":
    demo_nurture()
