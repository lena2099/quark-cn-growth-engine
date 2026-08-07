"""
品牌曝光监测 Agent — 夸克探险品牌声量 & 竞品监控
Brand Monitor Agent v1.0

功能:
  1. 统计夸克探险在搜索结果/内容中的曝光占比 (Share of Voice)
  2. 追踪竞品品牌的内容量和用户评价
  3. 计算 SOV 趋势变化
  4. 输出品牌健康度评分
"""

import os
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from config.settings import COMPETITOR_BRANDS, AI_CONFIG, ALERT_THRESHOLDS


class BrandMonitorAgent:
    """品牌声量监测 & 竞品分析"""

    def __init__(self):
        self.brands = COMPETITOR_BRANDS
        self.own_brand = [b for b in self.brands if b["is_own"]][0]
        self.competitors = [b for b in self.brands if not b["is_own"]]
        self.model = AI_CONFIG["model"]

    def analyze(self, raw_data: list[dict], report_date: date) -> dict:
        """
        统计各品牌在内容中的曝光情况
        """
        # Step 1: 对每条内容打品牌标签
        brand_mentions = defaultdict(lambda: {
            "count": 0,
            "content_titles": [],
            "platforms": Counter(),
            "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
        })

        total_branded_content = 0

        for record in raw_data:
            text = " ".join(
                str(record.get(f, ""))
                for f in ["title", "content", "keyword", "description", "summary"]
            ).lower()

            matched_brands = self._match_brands(text)
            if matched_brands:
                total_branded_content += 1

            for brand in matched_brands:
                brand_name = brand["name"]
                brand_mentions[brand_name]["count"] += 1
                brand_mentions[brand_name]["platforms"][record.get("platform", "unknown")] += 1
                if record.get("title"):
                    brand_mentions[brand_name]["content_titles"].append(
                        record["title"][:80]
                    )
                # 情感分析 (简单规则)
                sentiment = self._rule_sentiment(record, brand)
                brand_mentions[brand_name]["sentiment"][sentiment] += 1

        # Step 2: 计算 SOV (Share of Voice)
        sov = self._calculate_sov(brand_mentions)

        # Step 3: 夸克自身曝光详情
        own_data = brand_mentions.get(self.own_brand["name"], {
            "count": 0, "content_titles": [], "platforms": Counter(),
            "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
        })

        own_sov = sov.get(self.own_brand["name"], 0)

        # Step 4: 竞品排名
        competitor_ranking = self._rank_competitors(brand_mentions)

        # Step 5: 与历史对比
        prev_sov = self._load_previous_sov(report_date)
        sov_change = own_sov - prev_sov.get(self.own_brand["name"], 0) if prev_sov else 0

        # Step 6: 告警
        alerts = []
        if sov_change < -ALERT_THRESHOLDS["own_brand_share_drop"]:
            alerts.append(
                f"⚠️ 夸克 SOV 下降 {abs(sov_change):.1f} 个百分点, 建议增加内容投放"
            )

        for comp in competitor_ranking[:5]:
            if comp.get("is_own"):
                continue  # skip own brand
            prev_comp_sov = prev_sov.get(comp["name"], 0) if prev_sov else 0
            if comp["sov"] - prev_comp_sov > ALERT_THRESHOLDS["competitor_surge_pct"]:
                alerts.append(
                    f"📈 竞品「{comp['name']}」声量上升 +{comp['sov'] - prev_comp_sov:.1f}%"
                )

        # Step 7: AI 品牌健康度分析
        health_analysis = self._ai_brand_health(
            own_data, competitor_ranking, sov_change, report_date
        )

        result = {
            "date": str(report_date),
            "total_branded_content": total_branded_content,
            "own_brand": {
                "name": self.own_brand["name"],
                "name_en": self.own_brand["name_en"],
                "mentions": own_data["count"],
                "sov_pct": round(own_sov, 1),
                "sov_change_pct": round(sov_change, 1),
                "ranking": next(
                    (i + 1 for i, c in enumerate(competitor_ranking)
                     if c["name"] == self.own_brand["name"]),
                    len(competitor_ranking),
                ),
                "platform_breakdown": dict(own_data["platforms"]),
                "sentiment": own_data["sentiment"],
                "recent_titles": own_data["content_titles"][:10],
            },
            "sov_table": sov,
            "competitor_ranking": competitor_ranking,
            "alerts": alerts,
            "brand_health": health_analysis,
        }

        os.makedirs("data/processed", exist_ok=True)
        with open(f"data/processed/brand_monitor_{report_date}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    # ── 私有方法 ──

    def _match_brands(self, text: str) -> list[dict]:
        """在文本中匹配品牌"""
        matched = []
        for brand in self.brands:
            for alias in brand["aliases"]:
                if alias.lower() in text:
                    matched.append(brand)
                    break
        return matched

    def _rule_sentiment(self, record: dict, brand: dict) -> str:
        """基于规则的情感判断"""
        text = " ".join(
            str(record.get(f, "")) for f in ["title", "content", "comments_content"]
        ).lower()

        negative_words = ["差", "坑", "骗", "不值", "智商税", "失望", "垃圾", "后悔", "千万别"]
        positive_words = ["推荐", "值得", "完美", "震撼", "一生", "梦想", "太美了", "经验", "干货"]

        neg_score = sum(1 for w in negative_words if w in text)
        pos_score = sum(1 for w in positive_words if w in text)

        if neg_score > pos_score:
            return "negative"
        elif pos_score > neg_score:
            return "positive"
        return "neutral"

    def _calculate_sov(self, brand_mentions: dict) -> dict[str, float]:
        """计算 Share of Voice"""
        total = sum(v["count"] for v in brand_mentions.values())
        if total == 0:
            return {}
        return {
            name: round(data["count"] / total * 100, 1)
            for name, data in brand_mentions.items()
        }

    def _rank_competitors(self, brand_mentions: dict) -> list[dict]:
        """竞品排名"""
        ranking = []
        for brand in self.brands:
            data = brand_mentions.get(brand["name"], {"count": 0})
            ranking.append({
                "name": brand["name"],
                "name_en": brand["name_en"],
                "is_own": brand["is_own"],
                "mentions": data["count"],
                "platforms": dict(data.get("platforms", Counter())),
                "sentiment": data.get("sentiment", {}),
            })

        # 计算 SOV
        total = sum(r["mentions"] for r in ranking)
        for r in ranking:
            r["sov"] = round(r["mentions"] / total * 100, 1) if total > 0 else 0

        ranking.sort(key=lambda x: x["mentions"], reverse=True)
        return ranking

    def _load_previous_sov(self, report_date: date) -> dict[str, float]:
        """加载前一天的 SOV 数据"""
        prev_date = report_date - timedelta(days=1)
        path = f"data/processed/brand_monitor_{prev_date}.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                prev = json.load(f)
                return prev.get("sov_table", {})
        return {}

    def _ai_brand_health(
        self, own_data: dict, competitor_ranking: list,
        sov_change: float, report_date: date
    ) -> str:
        """AI 品牌健康度分析"""
        compact_ranking = [
            {"name": c["name"], "sov": c["sov"], "mentions": c["mentions"]}
            for c in competitor_ranking
        ]

        prompt = f"""
你是极地旅游品牌策略专家。分析夸克探险的品牌健康度并给出建议（150字以内）。

日期: {report_date}
夸克 SOV: {own_data.get('sov_pct', 0)}% | 变化: {sov_change:+.1f}%
竞品排名: {json.dumps(compact_ranking, ensure_ascii=False)}

请分析:
1. 夸克当前品牌健康度评价
2. 最值得警惕的竞品
3. 一条加强品牌曝光的建议
"""
        try:
            from agents.llm_client import chat
            return chat(
                prompt=prompt,
                model=self.model,
                temperature=0.3,
                max_tokens=300,
            ).strip()
        except Exception:
            return f"夸克探险 SOV {own_data.get('sov_pct', 0)}%, "
            f"行业排名 {own_data.get('ranking', '-')}. "
            f"建议增加 KOL 合作与优质内容产出。"
