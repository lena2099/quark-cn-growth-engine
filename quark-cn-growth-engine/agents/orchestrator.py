"""
Polar Growth OS — LLM Agent 编排层

将 Polar Customer Radar（规则引擎）升级为 GPT-4o 驱动的智能 Agent。
这是 Polar Growth OS 文档所描述的"AI 层"的核心实现：

  ┌──────────────────────────────────────────────┐
  │                 AI 层                         │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
  │  │LangChain │ │  Agent   │ │  Prompt  │     │
  │  │ 编排引擎  │ │  调度器   │ │  模板库   │     │
  │  └──────────┘ └──────────┘ └──────────┘     │
  └──────────────────────────────────────────────┘

三层协作：
  1. Prompt 模板库 — 专业领域知识的结构化表达
  2. LangChain 编排 — 链式调用（清洗→分析→生成）
  3. Agent 调度器 — 多 Agent 协作（客户分析×渠道BD×内容×销售）
"""
import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger("quark.agents.orchestrator")

# ═══════════════════════════════════════════════════════════
# Agent 类型定义
# ═══════════════════════════════════════════════════════════

class AgentRole(Enum):
    """四个核心 Agent，对应 Polar Growth OS 的四层架构"""
    CUSTOMER_ANALYST = "customer_analyst"    # 客户洞察 Agent
    CHANNEL_BD = "channel_bd"               # 渠道拓展 Agent
    CONTENT_CREATOR = "content_creator"      # 内容营销 Agent
    SALES_COACH = "sales_coach"             # 销售赋能 Agent


@dataclass
class AgentTask:
    """Agent 任务定义"""
    task_id: str
    role: AgentRole
    action: str                    # analyze / generate / recommend / score
    input_data: Dict               # 结构化输入
    context: Dict = field(default_factory=dict)  # 附加上下文
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentResult:
    """Agent 执行结果"""
    task_id: str
    role: AgentRole
    status: str                    # success / partial / error
    output: Dict                   # 结构化输出
    confidence: float = 1.0        # 置信度 0-1
    reasoning: str = ""            # 推理过程（可解释性）
    model_used: str = ""
    tokens_used: int = 0
    elapsed_ms: int = 0


# ═══════════════════════════════════════════════════════════
# Prompt 模板库
# ═══════════════════════════════════════════════════════════

PROMPT_TEMPLATES = {
    # ── 客户分析 Agent 提示词 ──
    "customer_profile": """你是一位极地旅行客户分析专家，专为 Quark Expeditions 中国市场服务。

请基于以下客户信息，生成一份结构化的客户画像分析报告：

【客户原始数据】
{raw_data}

【分析要求】
1. 客户分层：基于 RFM 模型（最近互动/频率/金额潜力）标注 A/B/C 级
2. 极地旅行意向：0-100 分制评估购买意愿
3. 消费能力推断：结合职业/年龄/历史旅行，估算预算区间
4. 决策周期：根据行为模式推断
5. 兴趣图谱：列出 3-5 个最相关的兴趣标签
6. 推荐航线：匹配最适合的 1-2 条 Quark 航线
7. 触达策略：给出下一步行动建议（具体到话术方向）

【输出格式】
返回 JSON：
{{
  "customer_tier": "A/B/C",
  "polar_intent_score": 0-100,
  "estimated_budget": "金额范围",
  "decision_cycle": "立即/周/月/季",
  "interest_tags": ["标签1", "标签2", ...],
  "recommended_routes": [
    {{"name": "航线名", "reason": "推荐理由", "price_range": "价格区间"}}
  ],
  "outreach_strategy": {{
    "channel": "触达渠道",
    "timing": "最佳时机",
    "angle": "切入角度",
    "sample_message": "示例消息片段"
  }},
  "risk_flags": ["潜在顾虑点"],
  "upsell_opportunities": ["升级/复购机会"]
}}""",

    "customer_batch_analysis": """你是 Quark Expeditions 中国市场的客户分析专家。

请对以下 {count} 位客户的资料进行批量分析，输出：
1. 客户分层分布（A/B/C 级各多少人）
2. Top 3 高价值客户的简要画像
3. 共性特征总结（年龄/职业/兴趣的集中趋势）
4. 本周应优先触达的 5 位客户及理由

【客户数据】
{batch_data}

输出 JSON 格式。""",

    # ── 渠道 BD Agent 提示词 ──
    "channel_scoring": """你是 Quark Expeditions 中国市场的渠道拓展专家。

请对以下潜在渠道合作伙伴进行评分和策略建议：

【渠道信息】
{channel_data}

【评分维度】（满分 100）
- 高净值人群密度 (35%)：渠道覆盖的高净值客户数量和质量
- 旅行消费意愿 (25%)：渠道客户对高端旅行的兴趣程度
- 竞品空白度 (20%)：该渠道竞品（庞洛/银海）的渗透程度
- 合作门槛 (20%)：签约难度、资源要求、排他性

【输出格式】
JSON:
{{
  "total_score": 0-100,
  "score_breakdown": {{
    "hnw_density": 0-35,
    "travel_willingness": 0-25,
    "competitor_gap": 0-20,
    "barrier_to_entry": 0-20
  }},
  "strategic_fit": "高度匹配/中度匹配/低度匹配",
  "recommended_approach": {{
    "first_contact_channel": "渠道",
    "pitch_angle": "切入角度",
    "expected_cycle": "预计签约周期",
    "key_concerns": ["对方可能的顾虑"]
  }},
  "cooperation_model": "包船/切位/联合营销/内容合作",
  "potential_volume": "预估年客量",
  "risk_assessment": "合作风险评估"
}}""",

    # ── 内容创作 Agent 提示词 ──
    "content_brief": """你是 Quark Expeditions 中国区内容策略专家。

请根据以下信息，生成本周的内容选题计划：

【目标受众画像】
{audience_profile}

【内容目标】
{content_goal}

【历史高绩效内容】
{top_performing}

【要求】
1. 生成 5 个选题建议（含标题、平台、形态、目标阶段）
2. 其中至少 2 个适配小红书，1 个适配公众号，1 个适配视频号/抖音
3. 每个选题标注"客户旅程阶段"（认知/兴趣/决策/下单/分享）
4. 给出 A/B 测试建议（哪两个标题可以同时测试）

输出 JSON。""",

    "content_multiformat": """你是 Quark Expeditions 的跨平台内容创作者。

请将以下核心素材，一键适配为 4 个平台的内容：

【核心素材】
{source_material}

【要求】
1. 公众号长文版（1500字，含标题/引言/3个小标题/CTA）
2. 小红书笔记版（500字，含标题/正文/3-5个Hashtag/引导评论）
3. 视频号脚本版（2分钟，含开场3秒钩子/主体/ending CTA）
4. 朋友圈图文版（150字+图片描述建议）

输出 JSON。""",

    "content_ab_test": """你是 Quark Expeditions 的 A/B 测试分析师。

请为同一选题生成 3 版标题和封面描述，用于测试：

【选题】
{topic}

【目标受众】
{audience}

要求：每个版本在"情感触发角度"上有所区别——版本A偏理性（数据/事实）、版本B偏感性（梦想/情感）、版本C偏身份（圈层/认同）。

输出 JSON。""",

    # ── 销售教练 Agent 提示词 ──
    "sales_talking_points": """你是 Quark Expeditions 最顶级的极地旅行销售顾问。

一位客户正在咨询，以下是客户信息和对话上下文：

【客户画像】
{customer_profile}

【对话上下文】
{conversation_context}

【客户当前问题】
{customer_question}

请提供：
1. 最佳回应话术（自然、专业、有温度）
2. 这个回答背后的策略思路（为什么这样回答）
3. 下一步追问建议（引导客户往成交方向走）
4. 需要避免的雷区（什么话绝对不能说）

输出 JSON。""",

    "objection_handler": """你是 Quark Expeditions 的异议处理专家。

客户提出了以下异议：

【异议内容】
{objection}

【异议类别】{category}  （价格/安全/体力/时间/竞品/其他）

【客户背景】
{customer_background}

请提供结构化的异议处理方案：

1. **共情回应**（先认可客户担忧，建立信任）
2. **事实澄清**（用数据/事实回应）
3. **价值重塑**（将话题从"价格"转向"价值"或从"恐惧"转向"安心"）
4. **行动引导**（给出一个低门槛的下一步）
5. **备用方案**（如果客户仍然不接受，Plan B 是什么）

输出 JSON。""",

    "sales_simulation": """你是 Quark Expeditions 的销售培训教练。

现在你要扮演一位{client_type}类型的潜在客户，与销售顾问进行模拟对话。

【客户设定】
- 年龄：{age}
- 职业：{profession}
- 旅行经验：{travel_experience}
- 对南极的了解程度：{polar_knowledge}
- 预算范围：{budget}
- 主要顾虑：{concerns}

【模拟规则】
1. 你会提出 3-5 个典型的疑问/异议
2. 在销售顾问回答后，你会根据回答质量决定是否继续深入或表示满意
3. 最后你会给出 1-100 分的评分和 3 条改进建议

请开始扮演客户，发出第一条消息。""",
}


# ═══════════════════════════════════════════════════════════
# LLM 客户端（抽象层）
# ═══════════════════════════════════════════════════════════

class LLMClient:
    """
    LLM 抽象客户端

    支持：
    - OpenAI GPT-4o / GPT-4o-mini
    - 本地模型（fallback）
    - 成本控制和 token 统计

    Polar Growth OS 文档建议：
    - 客户画像使用 GPT-4o（精度优先）
    - 批量标签使用 GPT-4o-mini（成本优先）
    - 缓存常用分析结果
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.model_map = {
            "analysis": "gpt-4o",          # 客户分析、渠道评分
            "generation": "gpt-4o",        # 内容创作、话术生成
            "batch": "gpt-4o-mini",        # 批量标签、分类
        }
        self._token_usage = 0
        self._call_count = 0
        self._cache = {}

    async def complete(
        self,
        prompt: str,
        system_role: str = "你是一位极地旅行行业专家，服务于 Quark Expeditions。",
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: str = "json_object",  # json_object or text
    ) -> Dict:
        """
        调用 LLM 完成分析/生成任务

        当前为模拟实现（无需 API key 即可演示架构）。
        实际部署时替换为 OpenAI SDK 调用。
        """
        cache_key = hash(prompt[:200] + model + str(temperature))
        if cache_key in self._cache:
            return self._cache[cache_key]

        self._call_count += 1

        # ═══════════════════════════════════════════
        # 实际部署代码（注释）
        # ═══════════════════════════════════════════
        # import openai
        # client = openai.AsyncClient(api_key=os.getenv("OPENAI_API_KEY"))
        # response = await client.chat.completions.create(
        #     model=model,
        #     messages=[
        #         {"role": "system", "content": system_role},
        #         {"role": "user", "content": prompt},
        #     ],
        #     temperature=temperature,
        #     max_tokens=max_tokens,
        #     response_format={"type": response_format},
        # )
        # self._token_usage += response.usage.total_tokens
        # return json.loads(response.choices[0].message.content)
        # ═══════════════════════════════════════════

        # 模拟返回（架构演示用，实际部署时删除此段）
        return {
            "status": "simulated",
            "message": "LLM call simulated — deploy with OPENAI_API_KEY to activate",
            "model_requested": model,
            "prompt_length": len(prompt),
        }

    def get_usage_stats(self) -> Dict:
        return {
            "total_calls": self._call_count,
            "total_tokens": self._token_usage,
            "cached_responses": len(self._cache),
        }


# ═══════════════════════════════════════════════════════════
# Agent 编排引擎
# ═══════════════════════════════════════════════════════════

class PolarGrowthAgentOrchestrator:
    """
    Polar Growth OS — Agent 编排引擎

    协调四个专业 Agent 完成端到端的增长任务。

    工作模式：
    1. 单 Agent 调用 — 单一任务（如：分析一个客户）
    2. 链式编排 — 多步骤流水线（如：扫描→分析→评分→建议）
    3. Agent 协作 — 多 Agent 并行分析同一问题（如：客户分析+渠道匹配+内容生成）
    """

    def __init__(self, config: dict = None):
        self.llm = LLMClient(config)
        self.prompts = PROMPT_TEMPLATES

    async def run_task(self, task: AgentTask) -> AgentResult:
        """执行单个 Agent 任务"""
        pass

    async def run_pipeline(self, tasks: List[AgentTask]) -> List[AgentResult]:
        """链式执行多个任务"""
        pass

    async def analyze_customer(self, customer_data: Dict) -> Dict:
        """
        客户分析 Agent（对应 Polar Growth OS 2.1）

        输入：客户碎片化数据（姓名/年龄/职业/互动记录/标签）
        输出：结构化客户画像 + 销售建议卡片

        这是 Polar Growth OS MVP 的核心流程：
          上传客户数据 → 自动清洗/去重 → 生成客户画像 →
          交叉分析（偏好×预算×决策周期） → 输出销售建议卡片
        """
        prompt = self.prompts["customer_profile"].format(
            raw_data=json.dumps(customer_data, ensure_ascii=False, indent=2)
        )

        result = await self.llm.complete(
            prompt=prompt,
            system_role="你是 Quark Expeditions 中国市场的顶级客户分析师，擅长从碎片化信息中构建精准客户画像。",
            model="gpt-4o",
            temperature=0.3,  # 分析任务用低温度保证一致性
        )

        return result

    async def analyze_customers_batch(self, customers: List[Dict]) -> Dict:
        """批量客户分析"""
        prompt = self.prompts["customer_batch_analysis"].format(
            count=len(customers),
            batch_data=json.dumps(customers, ensure_ascii=False, indent=2),
        )
        return await self.llm.complete(
            prompt=prompt,
            system_role="你是 Quark Expeditions 中国市场的客户分析专家。",
            model="gpt-4o-mini",
            temperature=0.3,
        )

    async def score_channel(self, channel_data: Dict) -> Dict:
        """渠道评分 Agent"""
        prompt = self.prompts["channel_scoring"].format(
            channel_data=json.dumps(channel_data, ensure_ascii=False, indent=2)
        )
        return await self.llm.complete(
            prompt=prompt,
            model="gpt-4o",
            temperature=0.4,
        )

    async def generate_content_brief(self, audience: Dict, goal: str, top_content: List) -> Dict:
        """内容选题生成"""
        prompt = self.prompts["content_brief"].format(
            audience_profile=json.dumps(audience, ensure_ascii=False),
            content_goal=goal,
            top_performing=json.dumps(top_content, ensure_ascii=False),
        )
        return await self.llm.complete(prompt=prompt, model="gpt-4o")

    async def adapt_content_multiformat(self, source: str) -> Dict:
        """一键多端内容适配"""
        prompt = self.prompts["content_multiformat"].format(source_material=source)
        return await self.llm.complete(prompt=prompt, model="gpt-4o")

    async def generate_ab_test(self, topic: str, audience: str) -> Dict:
        """A/B 测试变体生成"""
        prompt = self.prompts["content_ab_test"].format(topic=topic, audience=audience)
        return await self.llm.complete(prompt=prompt, model="gpt-4o-mini")

    async def generate_talking_points(
        self, customer_profile: Dict, conversation: str, question: str
    ) -> Dict:
        """实时话术生成"""
        prompt = self.prompts["sales_talking_points"].format(
            customer_profile=json.dumps(customer_profile, ensure_ascii=False),
            conversation_context=conversation,
            customer_question=question,
        )
        return await self.llm.complete(
            prompt=prompt,
            model="gpt-4o",
            temperature=0.6,
        )

    async def handle_objection(
        self, objection: str, category: str, customer_background: Dict
    ) -> Dict:
        """异议处理"""
        prompt = self.prompts["objection_handler"].format(
            objection=objection,
            category=category,
            customer_background=json.dumps(customer_background, ensure_ascii=False),
        )
        return await self.llm.complete(prompt=prompt, model="gpt-4o")

    async def start_sales_simulation(self, scenario: Dict) -> Dict:
        """销售模拟对练"""
        prompt = self.prompts["sales_simulation"].format(
            client_type=scenario.get("client_type", "企业主"),
            age=scenario.get("age", "50"),
            profession=scenario.get("profession", "企业主"),
            travel_experience=scenario.get("travel_experience", "去过30+国家"),
            polar_knowledge=scenario.get("polar_knowledge", "了解但未去过"),
            budget=scenario.get("budget", "20-30万"),
            concerns=scenario.get("concerns", "安全、体力、性价比"),
        )
        return await self.llm.complete(
            prompt=prompt,
            model="gpt-4o",
            temperature=0.8,  # 模拟对话需要更多变化
        )


# ═══════════════════════════════════════════════════════════
# MVP 演示
# ═══════════════════════════════════════════════════════════

async def demo_orchestrator():
    """演示 Agent 编排引擎的四大模块"""
    orch = PolarGrowthAgentOrchestrator()

    print("=" * 70)
    print("🧠 Polar Growth OS — Agent 编排引擎演示")
    print("=" * 70)

    # ── 模块 1: 客户分析 ──
    print("\n📊 模块 1/4: 客户分析 Agent")
    customer = {
        "name": "王总",
        "age": 52,
        "profession": "私募基金合伙人",
        "travel_history": ["冰岛(2023)", "非洲Safari(2022)", "瑞士滑雪(每年)"],
        "wecom_tags": ["南极兴趣-高意向", "预算-30万+", "企业家"],
        "interactions": [
            "2025-12: 收藏南极攻略3次",
            "2026-01: 参加线上极地分享会",
            "2026-03: 询问帝企鹅航线",
        ],
        "last_active": "2026-08-01",
    }
    result = await orch.analyze_customer(customer)
    print(f"   状态: {result.get('status')} | 模型: {result.get('model_requested')}")
    print(f"   此处应输出 → 客户画像卡片（A/B/C分级 + 极地意向分 + 推荐航线 + 触达策略）")

    # ── 模块 2: 渠道评分 ──
    print("\n🔍 模块 2/4: 渠道 BD Agent")
    channel = {
        "name": "招商银行私人银行",
        "type": "private_banking",
        "hnw_clients": ">100,000 (资产>1000万)",
        "travel_relevance": "私行权益含高端旅行定制",
        "competitor_presence": "庞洛已有合作，银海未渗透，Quark尚未接触",
        "barrier": "需要集团级合作签约，周期3-6个月",
    }
    result = await orch.score_channel(channel)
    print(f"   状态: {result.get('status')}")
    print(f"   此处应输出 → 渠道评分卡（4维打分 + 合作建议）")

    # ── 模块 3: 内容创作 ──
    print("\n📝 模块 3/4: 内容创作 Agent")
    result = await orch.generate_content_brief(
        audience={"age_range": "45-55", "profession": "企业主/高管", "interest": "极地旅行"},
        goal="提升 Quark 在中文社交媒体上的品牌认知度，突出直升机独家体验",
        top_content=[
            "《南极邮轮怎么选？》— 阅读量 12,000",
            "Ultramarine 直升机视频 — 播放量 85,000",
        ],
    )
    print(f"   状态: {result.get('status')}")
    print(f"   此处应输出 → 5个选题 + 平台分配 + AB测试方案")

    # ── 模块 4: 销售教练 ──
    print("\n🎯 模块 4/4: 销售教练 Agent")
    result = await orch.generate_talking_points(
        customer_profile={"tier": "A", "polar_score": 87, "budget": "30-50万", "concern": "安全"},
        conversation="客户：南极会不会很危险？我听说德雷克海峡风浪很大。",
        question="南极旅行安全吗？万一出事怎么办？",
    )
    print(f"   状态: {result.get('status')}")
    print(f"   此处应输出 → 最佳回应话术 + 策略思路 + 追问建议 + 雷区警示")

    print("\n" + "=" * 70)
    print(f"📊 LLM 用量统计: {json.dumps(orch.llm.get_usage_stats(), indent=2)}")
    print("=" * 70)
    print("\n💡 部署提示：设置 OPENAI_API_KEY 环境变量即可激活 GPT-4o 调用。")
    print("   当前为架构演示模式（模拟 LLM 返回）。")


if __name__ == "__main__":
    asyncio.run(demo_orchestrator())
