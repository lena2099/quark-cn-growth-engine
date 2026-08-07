"""
社媒数据采集 Agent — 多平台内容热度分析
Social Media Agent v1.0

功能:
  1. 按平台分组统计内容量
  2. 提取各平台热门内容 TOP N
  3. 分析评论/互动中的用户问题
  4. 识别高互动创作者
"""

import os
import json
from collections import Counter, defaultdict
from datetime import date
from config.settings import PLATFORMS, AI_CONFIG


class SocialMediaAgent:
    """社媒数据采集 & 热榜分析"""

    def __init__(self):
        self.platforms = PLATFORMS
        self.model = AI_CONFIG["model"]

    def analyze(self, raw_data: list[dict], report_date: date) -> dict:
        """
        按平台维度分析内容数据
        """
        # 按平台分组
        by_platform = defaultdict(list)
        for record in raw_data:
            platform = record.get("platform", "unknown")
            by_platform[platform].append(record)

        platform_results = {}
        total_content = 0
        all_top_creators = Counter()

        for platform_key, config in self.platforms.items():
            if not config["enabled"]:
                continue

            records = by_platform.get(platform_key, [])
            if not records:
                platform_results[platform_key] = {
                    "name": config["name"],
                    "content_count": 0,
                    "note": "当日无数据",
                }
                continue

            total_content += len(records)

            # 热门内容 TOP5 (按互动量排序)
            sorted_records = sorted(
                records,
                key=lambda r: self._engagement_score(r),
                reverse=True,
            )
            top_content = []
            for r in sorted_records[:5]:
                top_content.append({
                    "title": r.get("title", "无标题")[:80],
                    "author": r.get("author", "未知"),
                    "likes": int(r.get("likes", 0)),
                    "comments": int(r.get("comments", 0)),
                    "saves": int(r.get("saves", 0)),
                    "engagement": self._engagement_score(r),
                    "user_intent": self._detect_intent_from_comments(r),
                })
                if r.get("author"):
                    all_top_creators[r["author"]] += 1

            # 评论关键词分析
            comment_keywords = self._extract_comment_keywords(records)

            platform_results[platform_key] = {
                "name": config["name"],
                "content_count": len(records),
                "top_content": top_content,
                "comment_keywords": comment_keywords,
                "total_likes": sum(int(r.get("likes", 0)) for r in records),
                "total_comments": sum(int(r.get("comments", 0)) for r in records),
            }

        # AI 摘要
        summary = self._ai_summarize(platform_results, report_date)

        result = {
            "date": str(report_date),
            "total_content": total_content,
            "active_platforms": len([p for p in platform_results.values() if p.get("content_count", 0) > 0]),
            "platform_breakdown": platform_results,
            "top_creators": [{"name": name, "appearances": count}
                             for name, count in all_top_creators.most_common(10)],
            "summary": summary,
        }

        os.makedirs("data/processed", exist_ok=True)
        with open(f"data/processed/social_media_{report_date}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    # ── 私有方法 ──

    def _engagement_score(self, record: dict) -> int:
        """计算互动分: 点赞 + 评论*2 + 收藏*3"""
        likes = int(record.get("likes", 0))
        comments = int(record.get("comments", 0))
        saves = int(record.get("saves", 0))
        return likes + comments * 2 + saves * 3

    def _detect_intent_from_comments(self, record: dict) -> str:
        """从评论内容检测用户意图"""
        comments = str(record.get("comments_content", "")).lower()
        buy_signals = ["多少钱", "怎么买", "价格", "报名", "预订", "链接", "在哪里"]
        ask_signals = ["什么时候", "安全吗", "值得吗", "推荐吗", "好玩吗"]

        score = 0
        for s in buy_signals:
            if s in comments:
                score += 2
        for s in ask_signals:
            if s in comments:
                score += 1

        if score >= 4:
            return "强购买意图"
        elif score >= 2:
            return "中等兴趣"
        elif score >= 1:
            return "信息搜集"
        return "浏览"

    def _extract_comment_keywords(self, records: list[dict]) -> list[dict]:
        """提取评论中的高频关键词"""
        all_comments = " ".join(
            str(r.get("comments_content", "")) for r in records
        ).lower()

        target_phrases = [
            "多少钱", "怎么去", "安全吗", "值得吗", "签证",
            "装备", "季节", "推荐", "路线", "价格", "时间",
            "适合", "旅行社", "自由行", "跟团", "南极邮轮",
            "夸克", "海达路德", "庞洛", "银海",
        ]

        results = []
        for phrase in target_phrases:
            count = all_comments.count(phrase)
            if count > 0:
                results.append({"keyword": phrase, "count": count})
        results.sort(key=lambda x: x["count"], reverse=True)
        return results[:15]

    def _ai_summarize(self, platform_results: dict, report_date: date) -> str:
        """AI 生成社媒概览摘要"""
        compact = {}
        for k, v in platform_results.items():
            compact[k] = {
                "name": v["name"],
                "count": v.get("content_count", 0),
                "top_authors": [t.get("author") for t in v.get("top_content", [])[:3]],
            }

        prompt = f"""
你是中国市场社交媒体分析专家。简要总结南极旅游相关社媒动态（100字内）。

日期: {report_date}
各平台数据: {json.dumps(compact, ensure_ascii=False)}

请输出:
1. 哪个平台最活跃?
2. 用户最关注什么?
3. 一句策略建议
"""
        try:
            from agents.llm_client import chat
            return chat(
                prompt=prompt,
                model=self.model,
                temperature=0.3,
                max_tokens=250,
            ).strip()
        except Exception as e:
            return f"社媒数据概览: {len(compact)} 个平台有内容更新。"
