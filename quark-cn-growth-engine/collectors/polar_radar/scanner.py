"""
极地客户雷达 — 核心意图扫描引擎 (Polar Customer Radar v1.0)

核心理念：
  不是"搜索南极的人"才值得触达 — 而是任何在社交媒体上表露出
  "高净值+深度旅行升级+生命周期转折"信号的用户。

架构：
  社媒公开数据 → AI意图分析 → 多维评分 → 客户画像 → 培育建议
"""
import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import yaml

logger = logging.getLogger("quark.collectors.polar_radar")


# ═══════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════

@dataclass
class IntentSignal:
    """单条意图信号"""
    category: str          # strong_intent / implicit_intent / wealth_signal / negative
    subcategory: str       # polar_direct / travel_upgrade / business_owner ...
    pattern: str           # 匹配到的具体模式
    matched_text: str      # 匹配到的原文片段
    score: float           # 权重分


@dataclass
class PolarLead:
    """极地潜客"""
    id: str
    source: str            # xiaohongshu / douyin / wechat / zhihu / manual
    source_url: str

    # 原始信息
    raw_text: str = ""
    username: str = ""
    bio: str = ""

    # 分析结果
    signals: List[IntentSignal] = field(default_factory=list)
    score: float = 0.0
    tier: str = "cold"     # hot(≥70) / warm(40-69) / cold(<40) / nurture(<40但有潜力)

    # 画像
    age_range: str = ""          # 25-34 / 35-44 / 45-55 / 55+
    profession_category: str = "" # business_owner / executive / professional / unknown
    estimated_budget: str = ""   # 5-10万 / 10-20万 / 20-30万 / 30万+
    travel_level: str = ""       # 轻度/中度/重度/骨灰
    has_polar_awareness: bool = False  # 是否已有极地认知

    # 培育建议
    nurture_stage: str = "discovery"   # discovery / educate / engage / convert
    recommended_action: str = ""
    recommended_content: List[str] = field(default_factory=list)
    urgency: str = "low"         # immediate / week / month / quarter

    discovered_at: str = ""
    score_breakdown: Dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
# 意图扫描引擎
# ═══════════════════════════════════════════════════════════

class PolarRadarScanner:
    """极地客户雷达 — 主扫描引擎"""

    def __init__(self, config: dict = None):
        self.patterns = self._load_patterns()
        self._compiled_patterns = self._compile_patterns()

    def _load_patterns(self) -> dict:
        path = Path(__file__).parent.parent.parent / "config" / "intent_patterns.yaml"
        with open(path) as f:
            return yaml.safe_load(f)

    def _compile_patterns(self) -> dict:
        """预编译所有正则模式，加速匹配"""
        compiled = {}
        for category_key in ["strong_intent", "implicit_intent", "wealth_signals", "negative_signals"]:
            category = self.patterns.get(category_key, {})
            if isinstance(category, dict):
                for sub_key, sub in category.items():
                    if isinstance(sub, dict) and "patterns" in sub:
                        for i, pat in enumerate(sub["patterns"]):
                            key = f"{category_key}:{sub_key}:{i}"
                            try:
                                compiled[key] = {
                                    "regex": re.compile(pat, re.IGNORECASE),
                                    "category": category_key,
                                    "subcategory": sub_key,
                                    "score": sub.get("score", 0),
                                }
                            except re.error as e:
                                logger.warning(f"Invalid regex '{pat}': {e}")
        logger.info(f"Compiled {len(compiled)} intent patterns.")
        return compiled

    def scan_text(self, text: str, source: str = "unknown", url: str = "") -> PolarLead:
        """
        扫描一段文本，识别极地消费意图

        输入：用户帖子、评论、简介等任意文本
        输出：结构化的 PolarLead 对象（含评分、画像、建议）
        """
        lead_id = hashlib.md5((text + source).encode()).hexdigest()[:16]

        lead = PolarLead(
            id=lead_id,
            source=source,
            source_url=url,
            raw_text=text,
            discovered_at=datetime.now().isoformat(),
        )

        # Step 1: 匹配所有意图信号
        signals = []
        for key, comp in self._compiled_patterns.items():
            m = comp["regex"].search(text)
            if m:
                signals.append(IntentSignal(
                    category=comp["category"],
                    subcategory=comp["subcategory"],
                    pattern=key,
                    matched_text=m.group(0),
                    score=comp["score"],
                ))

        lead.signals = signals

        # Step 2: 评分
        lead.score, lead.score_breakdown = self._calculate_score(signals)

        # Step 3: 分级
        if lead.score >= 70:
            lead.tier = "hot"
        elif lead.score >= 40:
            lead.tier = "warm"
        elif lead.score >= 20:
            lead.tier = "nurture"
        else:
            lead.tier = "cold"

        # Step 4: 画像推断
        self._infer_profile(lead, text)

        # Step 5: 培育建议
        self._generate_nurture_plan(lead)

        return lead

    def _calculate_score(self, signals: List[IntentSignal]) -> Tuple[float, Dict]:
        """
        多维度评分模型

        满分 100 分：
        ┌──────────────────────┬──────┬──────────────────────────────┐
        │ 维度                  │ 最高 │ 说明                          │
        ├──────────────────────┼──────┼──────────────────────────────┤
        │ 1. 极地直接意图        │ 30分 │ 明确表达去南极/北极的需求       │
        │ 2. 旅行升级信号        │ 20分 │ 高端旅行偏好，隐含极地可能       │
        │ 3. 财富/身份信号        │ 25分 │ 消费能力和生活阶段匹配          │
        │ 4. 生命周期匹配        │ 15分 │ 退休/创业退出/人生转折点        │
        │ 5. 平台活跃信号        │ 10分 │ 互动深度、收藏、分享             │
        │ 6. 负面降权            │ -30分│ 价格敏感/环保反对/怕冷          │
        └──────────────────────┴──────┴──────────────────────────────┘
        """
        breakdown = {
            "polar_intent": 0,      # 极地直接意图
            "travel_upgrade": 0,    # 旅行升级
            "wealth_identity": 0,   # 财富身份
            "life_stage": 0,        # 生命周期
            "platform_activity": 0, # 平台活跃
            "negative_deduction": 0,# 负面降权
        }

        for sig in signals:
            cat = sig.category

            if cat == "strong_intent":
                if sig.subcategory == "polar_direct":
                    breakdown["polar_intent"] += sig.score
                elif sig.subcategory == "time_commitment":
                    breakdown["polar_intent"] += sig.score
                elif sig.subcategory == "social_proof":
                    breakdown["polar_intent"] += sig.score

            elif cat == "implicit_intent":
                if sig.subcategory == "travel_upgrade":
                    breakdown["travel_upgrade"] += sig.score
                elif sig.subcategory in ("photography_enthusiast", "science_education"):
                    breakdown["travel_upgrade"] += sig.score
                elif sig.subcategory == "life_stage":
                    breakdown["life_stage"] += sig.score
                elif sig.subcategory == "luxury_lifestyle":
                    breakdown["wealth_identity"] += sig.score

            elif cat == "wealth_signals":
                breakdown["wealth_identity"] += sig.score

            elif cat == "negative_signals":
                breakdown["negative_deduction"] += abs(sig.score)

        # 归一化上限
        for key, cap in [
            ("polar_intent", 30),
            ("travel_upgrade", 20),
            ("wealth_identity", 25),
            ("life_stage", 15),
            ("platform_activity", 10),
        ]:
            breakdown[key] = min(breakdown[key], cap)

        # 负面降权上限
        breakdown["negative_deduction"] = min(breakdown["negative_deduction"], 30)

        total = (
            breakdown["polar_intent"]
            + breakdown["travel_upgrade"]
            + breakdown["wealth_identity"]
            + breakdown["life_stage"]
            + breakdown["platform_activity"]
            - breakdown["negative_deduction"]
        )

        return max(0, min(total, 100)), breakdown

    def _infer_profile(self, lead: PolarLead, text: str):
        """从文本推断用户画像"""
        # 年龄推断
        age_patterns = {
            "25-34": [r"30[岁]|三十而立|刚.*30|奔三"],
            "35-44": [r"35[岁]|三十多|四十.*不到|奔四|刚.*40"],
            "45-55": [r"45[岁]|五十.*左右|年过半百|50[岁]|四十多"],
            "55+":   [r"退休|60[岁]|花甲|退休.*生活|孩子.*上大学|孩子.*工作"],
        }
        for age_range, pats in age_patterns.items():
            if any(re.search(p, text) for p in pats):
                lead.age_range = age_range
                break

        # 职业推断
        for subcat, title in [
            ("business_owner", "企业主"),
            ("executive", "企业高管"),
            ("professional", "专业人士"),
        ]:
            if any(sig.subcategory == subcat and sig.category == "wealth_signals"
                   for sig in lead.signals):
                lead.profession_category = title
                break

        # 预算推断
        if lead.score >= 80:
            lead.estimated_budget = "30万+"
        elif lead.score >= 65:
            lead.estimated_budget = "20-30万"
        elif lead.score >= 45:
            lead.estimated_budget = "10-20万"
        elif lead.score >= 25:
            lead.estimated_budget = "5-10万"
        else:
            lead.estimated_budget = "待评估"

        # 旅行级别推断
        travel_signals = sum(1 for sig in lead.signals
                            if sig.subcategory in ("travel_upgrade", "travel_history", "luxury_lifestyle"))
        if travel_signals >= 4:
            lead.travel_level = "骨灰级"
        elif travel_signals >= 2:
            lead.travel_level = "重度"
        elif travel_signals >= 1:
            lead.travel_level = "中度"
        else:
            lead.travel_level = "轻度"

        # 极地认知判断
        lead.has_polar_awareness = any(
            sig.subcategory == "polar_direct" for sig in lead.signals
        )

    def _generate_nurture_plan(self, lead: PolarLead):
        """
        根据评分和画像，自动生成培育路径

        核心原则：
          Hot (≥70)  → 立即分配销售顾问，1对1跟进
          Warm (40-69)→ 邀请进入极地社群，参加分享会
          Nurture (20-39) → 持续内容培育，不打扰
          Cold (<20)  → 不主动触达，等待自然转化
        """
        if lead.score >= 70:
            # HOT: 直接转化路径
            lead.nurture_stage = "convert"
            lead.urgency = "immediate"

            if lead.has_polar_awareness:
                lead.recommended_action = "🎯 立即分配销售顾问 | 1对1电话 | 推荐具体航线和舱位"
                lead.recommended_content = [
                    "《2026-2027南极季航线对比手册》",
                    "Ultramarine号直升机体验视频",
                    f"与您画像相似客户{lead.age_range}的真实体验分享",
                ]
            else:
                lead.recommended_action = "🎯 邀请参加最近一期极地线上/线下分享会 | 会后1对1跟进"
                lead.recommended_content = [
                    "《第一次南极旅行指南》",
                    "《为什么选择夸克探险？》品牌视频",
                    "极地摄影作品精选合集",
                ]

        elif lead.score >= 40:
            # WARM: 社群培育路径
            lead.nurture_stage = "engage"
            lead.urgency = "week"

            lead.recommended_action = "📩 邀请加入「极地探索」企业微信社群 | 发送定制化内容包"
            lead.recommended_content = [
                "《极地旅行100问》电子书",
                "月度极地线上分享会邀请函",
                f"根据您的{lead.travel_level}旅行经验推荐的极地路线",
            ]

        elif lead.score >= 20:
            # NURTURE: 长期内容培育
            lead.nurture_stage = "educate"
            lead.urgency = "month"

            lead.recommended_action = "📚 持续推送极地内容 | 关注但不打扰 | 等待信号增强"
            lead.recommended_content = [
                "极地动物纪录片推荐",
                "《全球7大极致旅行目的地》",
                "Quark探险队员日记系列",
            ]

        else:
            # COLD: 不主动触达
            lead.nurture_stage = "discovery"
            lead.urgency = "quarter"

            lead.recommended_action = "👀 持续观察 | 不主动触达 | 等待画像变化"
            lead.recommended_content = []

    def scan_batch(self, texts: List[Dict]) -> List[PolarLead]:
        """批量扫描"""
        leads = []
        for item in texts:
            lead = self.scan_text(
                text=item.get("text", ""),
                source=item.get("source", "unknown"),
                url=item.get("url", ""),
            )
            # 注入额外元数据
            if "username" in item:
                lead.username = item["username"]
            if "bio" in item:
                lead.bio = item["bio"]
            leads.append(lead)
        return leads

    def filter_actionable(self, leads: List[PolarLead], min_tier: str = "nurture") -> List[PolarLead]:
        """过滤出可操作的线索"""
        tier_order = {"hot": 0, "warm": 1, "nurture": 2, "cold": 3}
        threshold = tier_order.get(min_tier, 2)
        return [l for l in leads if tier_order.get(l.tier, 4) <= threshold]

    def summarize(self, leads: List[PolarLead]) -> Dict:
        """生成扫描总结"""
        hot = [l for l in leads if l.tier == "hot"]
        warm = [l for l in leads if l.tier == "warm"]
        nurture = [l for l in leads if l.tier == "nurture"]

        return {
            "scanned": len(leads),
            "hot": len(hot),
            "warm": len(warm),
            "nurture": len(nurture),
            "cold": len(leads) - len(hot) - len(warm) - len(nurture),
            "actionable": len(hot) + len(warm),
            "top_leads": [
                {
                    "id": l.id,
                    "score": l.score,
                    "tier": l.tier,
                    "source": l.source,
                    "age_range": l.age_range,
                    "profession": l.profession_category,
                    "budget": l.estimated_budget,
                    "action": l.recommended_action,
                    "urgency": l.urgency,
                    "text_snippet": l.raw_text[:120] + ("..." if len(l.raw_text) > 120 else ""),
                }
                for l in sorted(hot + warm, key=lambda x: x.score, reverse=True)[:10]
            ],
        }


# ═══════════════════════════════════════════════════════════
# 演示：极地客户雷达扫描模拟
# ═══════════════════════════════════════════════════════════

async def demo_scan():
    """模拟扫描社交媒体帖子 — 展示雷达的能力"""
    scanner = PolarRadarScanner()

    # 模拟帖子：各种真实场景
    test_posts = [
        {
            "username": "王总爱旅行",
            "bio": "去过47个国家，就差南极了。企业主，50岁，摄影爱好者",
            "text": "50岁了，把公司交给职业经理人，明年计划完成人生最后一块大陆——南极。有去过的朋友推荐下邮轮吗？预算不是问题，关键是要专业、人少、能多登陆。看到朋友坐夸克的船还有直升机，感觉很震撼。",
            "source": "xiaohongshu",
            "url": "https://xiaohongshu.com/post/example1",
        },
        {
            "username": "Lina爱摄影",
            "bio": "风光摄影师 | 大疆哈苏双修 | 走过非洲冰岛阿拉斯加",
            "text": "求推荐能拍到帝企鹅的南极线路！已经去过三次冰岛了，明年想挑战南极。希望有专业摄影向导，最好能深入冰架，普通跟团太浅了。",
            "source": "xiaohongshu",
            "url": "https://xiaohongshu.com/post/example2",
        },
        {
            "username": "退休规划中",
            "bio": "还有两年退休，已经开始规划人生下半场",
            "text": "退休后的第一年：南极➕北极一起走！开始存钱了，预算大概20万以内吧。有推荐的旅行社吗？",
            "source": "douyin",
            "url": "https://douyin.com/video/example3",
        },
        {
            "username": "环球张律师",
            "bio": "环球旅行135国 | 国际律所合伙人 | 穷游不穷体验",
            "text": "南极去了三次了，每次都有不同的震撼。这次坐的庞洛，服务是不错但太像豪华酒店了，缺了点探险的感觉。下次想试试夸克，听说直升机能去别人到不了的地方。",
            "source": "zhihu",
            "url": "https://zhihu.com/answer/example4",
        },
        {
            "username": "小王穷游日记",
            "bio": "学生党 | 穷游就是我的生活方式",
            "text": "南极好想去啊但是真的太贵了😭😭😭 有没有3万以内能去南极的办法？？？求攻略！！！",
            "source": "xiaohongshu",
            "url": "https://xiaohongshu.com/post/example5",
        },
        {
            "username": "创业十年陈",
            "bio": "连续创业者 | 去年公司B轮 | 家有俩娃",
            "text": "想带孩子体验一次改变人生的旅行。正在看非洲safari和南极，哪个更适合10岁孩子？主要是想让他看到不一样的世界，培养格局。",
            "source": "wechat",
            "url": "https://mp.weixin.qq.com/example6",
        },
        {
            "username": "健康生活李医生",
            "bio": "三甲医院心内科主任 | 旅行就是最好的养生",
            "text": "刚从肯尼亚回来，动物大迁徙太震撼了。下一站想去北极看极光，有医生同行吗？可以交流一下极地旅行对身心的影响。",
            "source": "xiaohongshu",
            "url": "https://xiaohongshu.com/post/example7",
        },
        {
            "username": "投行Linda",
            "bio": "香港投行MD | 周末飞全球 | 酒店控",
            "text": "今年已经飞了80段了，头等舱坐到麻木。想找一个真正能让人安静下来的旅行——没有信号、没有人打扰、只有冰和风的纯粹。是不是只有南极了？",
            "source": "xiaohongshu",
            "url": "https://xiaohongshu.com/post/example8",
        },
        {
            "username": "环保小卫士",
            "bio": "环保主义 | 拒绝过度消费",
            "text": "南极邮轮每年排放多少碳？极地旅游是不是在破坏最后一片净土？强烈建议禁止极地旅游！",
            "source": "zhihu",
            "url": "https://zhihu.com/answer/example9",
        },
        {
            "username": "旅行体验师大鹏",
            "bio": "旅行体验师 | 走过70国 | 专注高端定制",
            "text": "最近好多客户问南极，整理了一份各大邮轮公司的对比表：庞洛偏奢华、夸克偏探险、A21飞南极不晕船、银海管家服务...需要的点赞收藏。",
            "source": "xiaohongshu",
            "url": "https://xiaohongshu.com/post/example10",
        },
    ]

    print("\n" + "=" * 70)
    print("🔬 极地客户雷达 (Polar Customer Radar) — 演示扫描")
    print("=" * 70)

    leads = scanner.scan_batch(test_posts)
    actionable = scanner.filter_actionable(leads, min_tier="nurture")
    summary = scanner.summarize(leads)

    print(f"\n📊 扫描结果: {summary['scanned']}条帖子")
    print(f"   🔴 Hot (≥70):    {summary['hot']}人 — 立即跟进")
    print(f"   🟡 Warm (40-69):  {summary['warm']}人 — 社群培育")
    print(f"   🔵 Nurture:       {summary['nurture']}人 — 长期培育")
    print(f"   ⚪ Cold:          {summary['cold']}人 — 不主动触达")
    print(f"\n   ✅ 可操作线索: {summary['actionable']}人")

    print("\n" + "-" * 70)
    print("🏆 Top 线索详情:")
    print("-" * 70)

    for i, tl in enumerate(summary["top_leads"], 1):
        urgency_map = {"immediate": "⚡立即", "week": "📅本周", "month": "📆本月", "quarter": "🗓️本季"}
        print(f"\n{i}. [{tl['tier'].upper()}] 评分: {tl['score']:.0f}/100 | 来源: {tl['source']}")
        print(f"   年龄: {tl['age_range'] or '未知'} | 职业: {tl['profession'] or '未知'} | 预算: {tl['budget']}")
        print(f"   文本: \"{tl['text_snippet']}\"")
        print(f"   紧迫度: {urgency_map.get(tl['urgency'], tl['urgency'])}")
        print(f"   建议: {tl['action']}")

    # 展示第一个Hot lead的详细评分
    hot_leads = [l for l in leads if l.tier == "hot"]
    if hot_leads:
        print("\n" + "=" * 70)
        print(f"🔬 详细评分拆解 — \"{hot_leads[0].username}\" ({hot_leads[0].score:.0f}分)")
        print("=" * 70)
        print(f"识别到的意图信号 ({len(hot_leads[0].signals)}条):")
        for sig in hot_leads[0].signals:
            cat_name = {
                "strong_intent": "🎯 强意图",
                "implicit_intent": "🔍 隐性意图",
                "wealth_signals": "💰 财富信号",
                "negative_signals": "⚠️ 负面信号",
            }.get(sig.category, sig.category)
            print(f"  {cat_name} [{sig.subcategory}] +{sig.score:.0f} → \"{sig.matched_text[:80]}...\"")
        print(f"\n评分明细: {json.dumps(hot_leads[0].score_breakdown, ensure_ascii=False, indent=2)}")

    return leads


if __name__ == "__main__":
    asyncio.run(demo_scan())
