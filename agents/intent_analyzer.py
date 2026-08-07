"""
用户意图分析 Agent — AI 驱动的购买意图洞察
Intent Analyzer Agent v1.0 (核心模块)

功能:
  1. 用 GPT 分析每条用户内容的深层意图
  2. 提取用户画像: 年龄/性别/消费力/购买阶段
  3. 识别强购买信号 vs 观望信号
  4. 输出可执行的营销建议
"""

import os
import json
from collections import Counter, defaultdict
from datetime import date
from config.settings import USER_PROFILE_LABELS, AI_CONFIG


class IntentAnalyzerAgent:
    """AI 用户意图分析 — 从内容中提取购买信号"""

    def __init__(self):
        self.model = AI_CONFIG["intent_analysis"]["model"]
        self.temperature = AI_CONFIG["intent_analysis"]["temperature"]

    def analyze(self, raw_data: list[dict], report_date: date) -> dict:
        """
        对每一条有实质内容的数据进行意图分析
        """
        # 筛选有分析价值的记录 (有标题或内容)
        analyzable = [
            r for r in raw_data
            if r.get("title") or r.get("content") or r.get("comments_content")
        ]

        print(f"  待分析记录: {len(analyzable)} 条")

        # 批量分析 (每批 10 条以控制 API 开销)
        analyzed = []
        batch_size = 10
        for i in range(0, len(analyzable), batch_size):
            batch = analyzable[i : i + batch_size]
            results = self._analyze_batch(batch)
            analyzed.extend(results)

        # 聚合统计
        profile_distribution = self._aggregate_profiles(analyzed)
        intent_distribution = Counter()
        stage_distribution = Counter()
        high_intent_users = []

        for item in analyzed:
            intent_distribution[item.get("intent_level", "未知")] += 1
            stage_distribution[item.get("purchase_stage", "未知")] += 1
            if item.get("intent_level") in ("强购买信号", "高概率"):
                high_intent_users.append(item)

        # AI 生成策略建议
        strategy_suggestions = self._ai_generate_strategy(
            analyzed, profile_distribution, report_date
        )

        result = {
            "date": str(report_date),
            "analyzed_count": len(analyzed),
            "intent_distribution": dict(intent_distribution),
            "stage_distribution": dict(stage_distribution),
            "profile_distribution": profile_distribution,
            "high_intent_users": self._anonymize_users(high_intent_users[:10]),
            "strategy_suggestions": strategy_suggestions,
            "sample_insights": self._sample_insights(analyzed[:10]),
        }

        os.makedirs("data/processed", exist_ok=True)
        with open(f"data/processed/intent_analysis_{report_date}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    # ── 私有方法 ──

    def _analyze_batch(self, batch: list[dict]) -> list[dict]:
        """用 AI 分析一批用户内容"""
        items_text = []
        for idx, r in enumerate(batch):
            items_text.append({
                "id": idx,
                "title": str(r.get("title", ""))[:100],
                "content": str(r.get("content", ""))[:200],
                "comments": str(r.get("comments_content", ""))[:100],
            })

        prompt = f"""
你是中国市场高端旅行消费者洞察专家。分析以下用户在南极旅游相关内容中表现出的意图和画像。

对每条内容输出 JSON 格式:
{{
  "id": 数字,
  "age_group": "25-35|35-45|45-55|55-65|65+",
  "gender": "男性|女性|未知",
  "income_level": "高净值|中产偏高|中产|价格敏感",
  "travel_type": "奢华旅行者|摄影爱好者|冒险家|亲子家庭|退休旅者",
  "purchase_stage": "认知期|考虑期|比较期|决策期|复购期",
  "intent_level": "强购买信号|中等兴趣|观望|信息收集",
  "core_concern": "用户最关心的问题(10字内)",
  "recommended_action": "推荐的营销动作(15字内)"
}}

内容列表:
{json.dumps(items_text, ensure_ascii=False)}

只输出 JSON 数组，不要其他文字。
"""
        try:
            from agents.llm_client import chat
            raw = chat(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=2048,
                json_mode=True,
            )
            parsed = json.loads(raw)
            results = parsed if isinstance(parsed, list) else parsed.get("results", [])
            # 把原始数据合并回去
            for r in results:
                idx = r.get("id", 0)
                if idx < len(batch):
                    r["title"] = batch[idx].get("title", "")
                    r["platform"] = batch[idx].get("platform", "")
            return results
        except Exception as e:
            print(f"  ⚠️ 意图分析 API 调用失败: {e}")
            # 降级: 返回基础分析
            fallback = []
            for idx, r in enumerate(batch):
                text = (r.get("title", "") + r.get("content", "")).lower()
                intent = "信息收集"
                for s in ["多少钱", "价格", "预订", "报名"]:
                    if s in text:
                        intent = "强购买信号"
                        break
                for s in ["推荐", "哪家", "怎么选"]:
                    if s in text:
                        intent = "中等兴趣"
                        break
                fallback.append({
                    "id": idx,
                    "age_group": "35-45",
                    "gender": "未知",
                    "income_level": "中产偏高",
                    "travel_type": "奢华旅行者",
                    "purchase_stage": "考虑期",
                    "intent_level": intent,
                    "core_concern": "价格与体验",
                    "recommended_action": "提供产品对比资料",
                    "title": r.get("title", ""),
                    "platform": r.get("platform", ""),
                })
            return fallback

    def _aggregate_profiles(self, analyzed: list[dict]) -> dict:
        """聚合用户画像分布"""
        profile = {}
        for label in ["age_group", "gender", "income_level", "travel_type", "purchase_stage"]:
            counter = Counter()
            for item in analyzed:
                val = item.get(label)
                if val:
                    counter[val] += 1
            profile[label] = dict(counter.most_common())
        return profile

    def _anonymize_users(self, users: list[dict]) -> list[dict]:
        """脱敏用户信息"""
        for u in users:
            u.pop("id", None)
        return users

    def _sample_insights(self, analyzed: list[dict]) -> list[dict]:
        """提取有代表性的洞察片段"""
        samples = []
        for item in analyzed[:5]:
            samples.append({
                "snippet": item.get("title", "")[:60],
                "age_group": item.get("age_group"),
                "intent_level": item.get("intent_level"),
                "core_concern": item.get("core_concern"),
                "recommended_action": item.get("recommended_action"),
            })
        return samples

    def _ai_generate_strategy(
        self, analyzed: list[dict],
        profile_distribution: dict, report_date: date
    ) -> str:
        """AI 生成营销策略建议"""
        high_intent = sum(
            1 for a in analyzed if a.get("intent_level") in ("强购买信号", "高概率")
        )
        total = len(analyzed)

        prompt = f"""
你是极地旅游营销策略专家。基于以下数据, 用中文给出今日 3-5 条可执行的营销建议。

日期: {report_date}
分析用户总数: {total}
强购买意图用户: {high_intent} ({round(high_intent/total*100) if total else 0}%)
用户画像分布: {json.dumps(profile_distribution, ensure_ascii=False)}

请输出:
1. 今日最值得跟进的用户群体
2. 推荐内容方向
3. 具体行动建议
总字数控制在 200 字以内。
"""
        try:
            from agents.llm_client import chat
            return chat(
                prompt=prompt,
                model=self.model,
                temperature=0.4,
                max_tokens=400,
            ).strip()
        except Exception as e:
            return f"建议优先跟进 {high_intent} 位强购买意图用户，重点投放南极旅行价值教育类内容。"
