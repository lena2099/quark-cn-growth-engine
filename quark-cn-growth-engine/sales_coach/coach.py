"""
AI 销售教练 (Sales Coach Agent)

对应 Polar Growth OS 2.4 节：
  定位：让每个销售都具备顶级顾问的专业度。

四个能力：
  1. 实时话术提示 — 客户提问 → AI 检索知识库 → 弹窗推荐最佳回应
  2. 异议处理库 — 50+ 高频异议的结构化回应框架
  3. 模拟对练 — AI 扮演客户，销售练习并获评分
  4. 跟单助手 — 自动生成个性化跟进消息
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("quark.agents.sales_coach")


# ═══════════════════════════════════════════════════════════
# 异议处理库（50+ 高频异议）
# ═══════════════════════════════════════════════════════════

OBJECTION_LIBRARY = {
    # ── 价格异议 ──
    "too_expensive": {
        "category": "价格",
        "patterns": ["太贵", "这么贵", "不划算", "不值得", "花这么多钱", "别的船便宜很多"],
        "structure": {
            "empathize": "完全理解您的感受。南极旅行的确是一笔不小的投入，很多客户在了解之前也有同样的想法。",
            "clarify": "但您知道吗——南极旅行不是一次度假，而是一生一次的探险。30万的投入，买的是地球上最极致的体验。而且这个价格包含了：国际机票、所有餐饮、专家讲解、探险装备、甚至直升机体验。",
            "reframe": "如果您把它看作一次'旅行'，确实不便宜。但如果您把它看作对人生的投资——对视野、对故事、对家庭传承的投资——30万可能是您今年最值的花销。",
            "action": "不如这样：我给您发一份详细的价格拆解，所有费用一目了然。您会发现，Quark 的性价比其实是业内最高的——因为我们包含的探险项目比别人多30%以上。",
            "fallback": "如果预算确实有考虑，我们可以聊一下明年早鸟价——提前18个月预订可以省15%。或者从入门航线开始，先体验，再升级。",
        },
    },
    "other_ship_cheaper": {
        "category": "价格/竞品",
        "patterns": ["别的船", "庞洛多少", "银海多少", "为什么比XX贵", "同样南极"],
        "structure": {
            "empathize": "您真的很专业，做了不少功课。不同船公司的价格差异确实挺大的。",
            "clarify": "关键在于——您买的是'去南极'还是'探索南极'。便宜的船一般是200-500人大船，每天只有1-2次登陆，而且每次只能在岸上待45-90分钟。Quark是100-200人的小船，每天可以登陆2-3次，每次可以待2-3小时。更重要的是，只有Quark有双直升机，能带您到别人去不了的地方。",
            "reframe": "打个比方：同样是去南极，便宜的船像是'在景区门口拍了张照片'，Quark是'走进了景区最深处'。多花的钱，买的是别人看不到的风景。",
            "action": "我发您一份详细的邮轮对比表，把Quark和市面上所有船逐一对比——看完您会发现，Quark不是贵，是'值'。",
            "fallback": "如果预算先锁定在15万以内，我们有一条2027年的早鸟入门航线，100人小船，3次登陆，也是Quark的品质。",
        },
    },

    # ── 安全异议 ──
    "safety_concern": {
        "category": "安全",
        "patterns": ["安全吗", "危险", "出事", "翻船", "冰崩", "德雷克", "风浪"],
        "structure": {
            "empathize": "这个问题问得特别好。安全是所有探险旅行最重要的事，您能关心这个问题说明您是认真考虑南极的。",
            "clarify": "Quark有30年的极地探险经验，零安全事故。我们的探险队员是业内规模最大的，平均有15年以上极地工作经验。每条船都配备最先进的冰区导航系统、卫星通讯、以及完整的医疗设施——包括一位随船医生。",
            "reframe": "实际上，南极旅行比大多数人想象的安全得多。IAATO（国际南极旅游组织协会）有极其严格的安全标准，所有运营商都必须遵守。您担心的德雷克海峡——如果实在怕晕船，我们可以安排飞越德雷克海峡的航线。",
            "action": "我给您看一段我们探险队长讲解安全流程的视频，3分钟就能让您彻底放心。",
            "fallback": "如果您对长途航行有顾虑，可以考虑'飞南极'航线——飞越德雷克海峡，完全不晕船。",
        },
    },
    "age_fitness": {
        "category": "体力",
        "patterns": ["年纪大", "体力", "走不动", "太累", "不适合", "身体", "吃不消"],
        "structure": {
            "empathize": "这个顾虑很实际。很多客户在50多岁去南极之前都有同样的担心。",
            "clarify": "实际上，南极旅行并不是极限运动。每天的活动是根据您的体力来安排的——可以是轻松的冲锋舟巡游（坐在船上不动），也可以是短途冰原徒步。我们的探险队员会评估每个人的体力，给出最合适的建议。Quark的客户平均年龄是55岁，最年长的客人86岁——他走完了全程。",
            "reframe": "南极最珍贵的不是'征服'，而是'感受'。坐在冲锋舟上静静地看着冰川崩塌，那种震撼和体力无关。",
            "action": "我给您发一段我们60岁客户拍的视频——您看看他们的节奏和状态，就知道完全不用担心。",
            "fallback": "如果不想走太多路，我们可以安排以巡游为主的航线——您坐在船上就能看到企鹅、海豹、鲸鱼。",
        },
    },
    "time_commitment": {
        "category": "时间",
        "patterns": ["没时间", "太久", "请假", "走不开", "时间太长", "公司离不开"],
        "structure": {
            "empathize": "您是企业主/高管，时间确实是最稀缺的资源。",
            "clarify": "南极旅行的确是15-20天的投入。但请思考：您上一次真正'断开一切'是什么时候？没有邮件、没有会议、没有电话——完全属于自己的时间。Quark的南极航线不仅是旅行，更是一次强制性的'数字排毒'。",
            "reframe": "很多客户回来后说——在南极的20天，比在办公室的200天更有价值。因为您不是在'浪费时间'，而是在充电、在思考、在获得新的视角。很多企业家都是在南极想通了公司下一步的方向。",
            "action": "我们有8天和11天的入门航线，时间更可控。我帮您看看哪些排期刚好在您的低峰期？",
            "fallback": "如果您时间真的排不开，可以先预订2028年的位置——早订不仅可以选最好的舱位，还能锁定现在的价格。",
        },
    },

    # ── 竞品异议 ──
    "ponant_comparison": {
        "category": "竞品",
        "patterns": ["庞洛", "PONANT", "法国船", "奢华", "管家", "庞洛怎么样"],
        "structure": {
            "empathize": "庞洛确实是一家优秀的邮轮公司，法式奢华体验非常出色。",
            "clarify": "关键区别在于——庞洛的核心是'奢华酒店搬到海上'，Quark的核心是'最极致的极地探险'。庞洛有管家服务和米其林餐，Quark有业内唯一双直升机和最多登陆次数。如果您去南极是为了'被服务'——选庞洛。如果您去南极是为了'看见别人看不见的世界'——选Quark。",
            "reframe": "很多客户的选择是：第一次坐庞洛体验'奢华南极'，第二次坐Quark体验'真正的南极'。这两家不是竞争关系，而是互补关系。",
            "action": "我给您发一个真实的客户故事——一位之前坐庞洛的客人，第二次选了Quark，看看他的感受对比。",
            "fallback": "其实如果您想要'奢华+探险'的平衡，Quark的Ultramarine号套房配置不输庞洛，但有直升机——等于用差不多的价格多了一个独一无二的体验。",
        },
    },
}


# ═══════════════════════════════════════════════════════════
# 销售教练 Agent
# ═══════════════════════════════════════════════════════════

class SalesCoach:
    """
    AI 销售教练

    使用方法：
      coach = SalesCoach()
      response = coach.handle_objection("太贵了", customer_context)
      print(response["best_response"])
    """

    def __init__(self, llm_client=None):
        self.objections = OBJECTION_LIBRARY
        self.llm = llm_client

    # ── 能力 1: 实时异议处理 ──
    def handle_objection(self, text: str, customer_context: Dict = None) -> Dict:
        """
        输入客户原话 → 匹配异议类型 → 返回结构化回应

        返回格式：
        {
          "matched_category": "价格",
          "matched_type": "too_expensive",
          "confidence": 0.92,
          "best_response": "...",    # 最佳回应话术
          "strategy": "...",         # 策略思路
          "next_question": "...",    # 建议追问
          "red_flags": [...],        # 雷区
          "fallback": "..."          # 备选方案
        }
        """
        # Step 1: 匹配异议类型
        matched = self._match_objection(text)
        if not matched:
            return self._generic_response(text, customer_context)

        obj_type, confidence = matched

        # Step 2: 获取结构化回应
        obj = self.objections[obj_type]
        structure = obj["structure"]

        # Step 3: 个性化（如果有客户上下文）
        response = self._personalize(structure, customer_context)

        return {
            "matched_category": obj["category"],
            "matched_type": obj_type,
            "confidence": round(confidence, 2),
            "best_response": response["best"],
            "strategy": response["strategy"],
            "next_question": response["next"],
            "red_flags": [
                "❌ 不要直接说'别的船不安全'——这会显得攻击竞品",
                "❌ 不要说'这个价格已经很便宜了'——高净值客户反感被暗示买不起",
                "❌ 不要急着降价——先建立价值，价格是最后一步",
            ],
            "fallback": structure.get("fallback", ""),
        }

    def _match_objection(self, text: str) -> Optional[tuple]:
        """匹配异议到知识库"""
        best_match = None
        best_score = 0

        for obj_type, obj in self.objections.items():
            for pattern in obj["patterns"]:
                if pattern in text or any(char in text for char in pattern.split("|")):
                    score = len(pattern) / len(text) if len(text) > 0 else 0
                    # 给更长的匹配更高的分数
                    score = min(score * 5, 1.0)
                    if score > best_score:
                        best_score = score
                        best_match = obj_type

        if best_match:
            return (best_match, max(best_score, 0.6))
        return None

    def _personalize(self, structure: Dict, context: Dict = None) -> Dict:
        """根据客户上下文个性化回应"""
        name = (context or {}).get("name", "")
        profession = (context or {}).get("profession", "")

        best = structure["empathize"] + "\n\n" + structure["clarify"] + "\n\n" + structure["reframe"]

        strategy = structure["clarify"][:80] + "..."
        next_q = structure["action"]

        # 如果有客户名字，个性化开头
        if name:
            best = best.replace("完全理解", f"{name}总，完全理解", 1)

        return {"best": best, "strategy": strategy, "next": next_q}

    def _generic_response(self, text: str, context: Dict = None) -> Dict:
        """未匹配知识库时的通用回应"""
        return {
            "matched_category": "其他",
            "matched_type": "unknown",
            "confidence": 0.3,
            "best_response": f"这个问题很关键。让我先确认一下您的具体关注点——您最关心的是哪个方面？这样我能给您更精准的信息。",
            "strategy": "未匹配到标准异议 → 引导客户澄清 → 再针对性回应",
            "next_question": "能再多说说您的具体考虑吗？",
            "red_flags": ["❌ 不要猜客户意思——先问清楚再回"],
            "fallback": "我请我们的极地专家来回答这个问题，他比我更了解细节。",
        }

    # ── 能力 2: 跟单助手 ──
    def generate_followup(self, customer: Dict, stage: str) -> str:
        """根据客户阶段自动生成跟进消息"""
        templates = {
            "initial_contact": f"""
{customer.get('name', '您好')}您好！我是Quark Expeditions的极地旅行顾问。

注意到您最近对南极旅行有关注。刚好我们这周六有一场线上分享会——南极探险队长会亲自讲解2027年的独家航线，还有直升机冰原体验的视频首播。

不打扰您，如果感兴趣，我给您发一份邀请函？""",

            "after_sharing": f"""
{customer.get('name', '您好')}您好！上周的分享会很精彩，看到您全程在线，不知道感受如何？

很多客户听完后最感兴趣的是Ultramarine号的直升机体验——全球唯一，可以直接降落在常规船到不了的冰原深处。

您如果有任何疑问，随时问我——我在极地旅游行业做了5年，知无不言。""",

            "decision_push": f"""
{customer.get('name', '您好')}，有个小提醒——

2027年南极季的早鸟价这周五截止。目前{customer.get('preferred_route', '南极半岛经典11天')}航线还剩最后3个舱位。

如果您还在考虑，我建议先把舱位锁住（不需要付全款，定金1万即可锁定），这样进可攻退可守。错过这波，同样的舱位下一轮要贵15%。

您看需要我帮您预留一个吗？""",

            "reactivation": f"""
{customer.get('name', '您好')}，好久不见！

最近我们有一位52岁的企业家客户刚从南极回来，他说了一句话让我印象特别深：'去了40个国家，南极是唯一一个让我流泪的。'

突然想到您之前也对南极感兴趣——2027年我们新开了一条威德尔海帝企鹅航线，非常特别。您要不要看看？完全不用有压力。""",
        }

        return templates.get(stage, templates["initial_contact"]).strip()

    # ── 能力 3: 模拟对练评分 ──
    def score_sales_response(
        self,
        customer_question: str,
        sales_response: str,
        expected_framework: Dict = None,
    ) -> Dict:
        """
        评估销售回答质量

        评分维度：
        - 共情度 (0-25): 是否先认可客户感受
        - 专业度 (0-25): 信息是否准确、有说服力
        - 价值重塑 (0-25): 是否把话题从问题转向价值
        - 推进力 (0-25): 是否有明确的下一步引导

        总分 100
        """
        scores = {
            "empathy": self._score_empathy(sales_response),
            "professionalism": self._score_professionalism(sales_response, customer_question),
            "value_reframing": self._score_value_reframing(sales_response),
            "advancement": self._score_advancement(sales_response),
        }
        total = sum(scores.values())

        if total >= 85:
            grade = "🏆 S级 — 顶级顾问水平"
        elif total >= 70:
            grade = "🌟 A级 — 优秀，细节可打磨"
        elif total >= 55:
            grade = "👍 B级 — 基本合格，策略需加强"
        else:
            grade = "📚 C级 — 需要刻意练习"

        return {
            "total_score": total,
            "grade": grade,
            "breakdown": scores,
            "improvements": self._generate_improvements(scores, sales_response),
        }

    def _score_empathy(self, response: str) -> int:
        """评估共情度"""
        score = 0
        empathy_keywords = ["理解", "明白", "确实", "很多客户", "正常的", "我也觉得"]
        if any(kw in response for kw in empathy_keywords):
            score += 15
        if len(response) > 20 and not response.startswith("不对"):
            score += 10
        return min(score, 25)

    def _score_professionalism(self, response: str, question: str) -> int:
        score = 0
        if "Quark" in response or "夸克" in response:
            score += 8
        if any(word in response for word in ["直升机", "IAATO", "探险队", "30年", "登陆"]):
            score += 10
        if len(response) > 80:
            score += 7
        return min(score, 25)

    def _score_value_reframing(self, response: str) -> int:
        score = 0
        if any(word in response for word in ["不是", "而是", "投资", "一生", "体验", "值得"]):
            score += 12
        if "价" in response and "值" in response:
            score += 8
        if "独特" in response or "唯一" in response or "只有" in response:
            score += 5
        return min(score, 25)

    def _score_advancement(self, response: str) -> int:
        score = 0
        if any(word in response for word in ["不如", "我给您", "要不要", "试试", "安排"]):
            score += 15
        if "?" in response[-50:]:
            score += 10
        return min(score, 25)

    def _generate_improvements(self, scores: Dict, response: str) -> List[str]:
        improvements = []
        if scores["empathy"] < 20:
            improvements.append("💡 开头先共情：'完全理解您的感受...' 这样客户会觉得你站在他这边")
        if scores["professionalism"] < 20:
            improvements.append("💡 增加专业细节：提到具体数字（30年/直升机/登陆次数）比泛泛而谈更有说服力")
        if scores["value_reframing"] < 20:
            improvements.append("💡 做价值重塑：不要说'不贵'，说'这不是花费，是投资'——把话题从价格转向体验")
        if scores["advancement"] < 20:
            improvements.append("💡 结尾要有行动引导：每个回应结尾都应该有一个低门槛的下一步——'我发您一个视频'/'我们约个电话'")
        if not improvements:
            improvements.append("💡 已经非常优秀！可以尝试在回应中加入一个客户故事作为案例，效果会更好。")
        return improvements


# ═══════════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════════

def demo_sales_coach():
    coach = SalesCoach()

    print("=" * 70)
    print("🎯 AI 销售教练 — 演示")
    print("=" * 70)

    # ── 演示 1: 异议处理 ──
    print("\n📋 演示 1: 实时异议处理")
    test_objections = [
        "30万太贵了吧，别的船好像便宜很多",
        "南极会不会很危险？我听说有人出过事",
        "我55岁了，体力跟不上吧",
        "庞洛好像更奢华，你们怎么比？",
    ]

    for obj in test_objections:
        result = coach.handle_objection(obj, {"name": "李先生", "profession": "企业主"})
        print(f"\n客户: \"{obj}\"")
        print(f"匹配: {result['matched_type']} ({result['matched_category']}) | 置信度: {result['confidence']}")
        print(f"回应 (前120字): {result['best_response'][:120]}...")
        print(f"追问: {result['next_question'][:80]}...")

    # ── 演示 2: 跟单消息生成 ──
    print("\n\n📋 演示 2: 跟单消息自动生成")
    customer = {
        "name": "王总",
        "profession": "企业主",
        "preferred_route": "南极半岛经典11天",
        "budget": "20-30万",
    }

    for stage in ["initial_contact", "after_sharing", "decision_push", "reactivation"]:
        msg = coach.generate_followup(customer, stage)
        print(f"\n阶段: {stage}")
        print(f"消息: {msg[:150]}...")

    # ── 演示 3: 回答评分 ──
    print("\n\n📋 演示 3: 销售回答质量评分")
    test_responses = [
        {
            "question": "南极太贵了，30万不值得。",
            "response": "您说得对，30万确实不是一笔小钱。但很多客户去完回来说——这不是花掉的30万，是换了一种方式陪伴自己的30万。Quark的航线每天能登陆2-3次，还有直升机可以到别人到不了的地方。要不我先给您发个视频感受一下？",
        },
        {
            "question": "南极太贵了，30万不值得。",
            "response": "不贵啊，你去别的地方也要花钱。南极就这个价。",
        },
    ]

    for i, tr in enumerate(test_responses, 1):
        result = coach.score_sales_response(tr["question"], tr["response"])
        print(f"\n回答 {i} — 得分: {result['total_score']}/100 | {result['grade']}")
        print(f"  共情:{result['breakdown']['empathy']} 专业:{result['breakdown']['professionalism']} 价值:{result['breakdown']['value_reframing']} 推进:{result['breakdown']['advancement']}")
        for imp in result["improvements"]:
            print(f"  {imp}")


if __name__ == "__main__":
    demo_sales_coach()
