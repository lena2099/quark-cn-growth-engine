"""
关键词雷达 Agent — 监控三级关键词热度变化，发现消费趋势
Keyword Radar Agent v1.0

功能：
  1. 对每条原始数据按三级关键词库打标
  2. 计算各关键词的提及量和环比变化
  3. 识别热度飙升关键词 (surge detection)
  4. 输出热度变化原因分析 (AI 驱动)
"""

import os
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from config.settings import KEYWORD_LIBRARY, AI_CONFIG, ALERT_THRESHOLDS


class KeywordRadarAgent:
    """关键词雷达 — 发现极地消费需求"""

    def __init__(self):
        self.keyword_library = self._flatten_keywords(KEYWORD_LIBRARY)
        self.surge_threshold = ALERT_THRESHOLDS["keyword_surge_pct"]
        self.model = AI_CONFIG["model"]
        self.temperature = AI_CONFIG["temperature"]

    def analyze(self, raw_data: list[dict], report_date: date) -> dict:
        """
        输入: 原始数据列表 [{platform, keyword, title, content, ...}, ...]
        输出: 关键词热度分析结果
        """
        # Step 1: 打标 — 每条数据匹配到关键词类别
        tagged = self._tag_records(raw_data)

        # Step 2: 统计 — 每个关键词的提及量
        current_counts = Counter()
        category_counts = Counter()
        for record in tagged:
            for kw in record.get("matched_keywords", []):
                current_counts[kw] += 1
            for cat in record.get("matched_categories", []):
                category_counts[cat] += 1

        # Step 3: 加载历史数据做环比
        prev_counts = self._load_previous_counts(report_date)
        changes = self._compute_changes(current_counts, prev_counts)

        # Step 4: 识别飙升关键词
        surges = self._detect_surges(changes)

        # Step 5: AI 分析热度变化原因
        analysis_text = self._ai_analyze_causes(tagged, changes, surges, report_date)

        # Step 6: 组装输出
        result = {
            "date": str(report_date),
            "total_mentions": sum(current_counts.values()),
            "category_breakdown": dict(category_counts),
            "keyword_breakdown": dict(current_counts.most_common(30)),
            "changes": changes,
            "surge_keywords": surges,
            "ai_analysis": analysis_text,
            "alerts": self._generate_alerts(changes, surges),
        }
        # 保存处理结果
        self._save_results(result, report_date)
        return result

    # ── 私有方法 ──

    def _flatten_keywords(self, library: dict) -> dict[str, list[str]]:
        """将关键词库展开为 {keyword: [categories], ...}"""
        flat = {}
        for category, config in library.items():
            for kw in config["keywords"]:
                kw_lower = kw.lower()
                if kw_lower not in flat:
                    flat[kw_lower] = []
                flat[kw_lower].append(category)
        return flat

    def _tag_records(self, records: list[dict]) -> list[dict]:
        """给每条记录打上关键词标签"""
        for record in records:
            matched_kw = set()
            matched_cat = set()
            # 搜索内容字段
            text = " ".join(
                str(record.get(f, ""))
                for f in ["title", "content", "keyword", "description", "summary"]
            ).lower()

            for kw, cats in self.keyword_library.items():
                if kw in text:
                    matched_kw.add(kw)
                    for c in cats:
                        matched_cat.add(c)

            record["matched_keywords"] = list(matched_kw)
            record["matched_categories"] = list(matched_cat)
        return records

    def _load_previous_counts(self, report_date: date) -> Counter:
        """加载前一周平均数据用于对比"""
        prev_data = []
        for i in range(1, 8):
            d = report_date - timedelta(days=i)
            path = f"data/processed/keyword_counts_{d}.json"
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    prev_data.append(json.load(f))

        if not prev_data:
            return Counter()

        # 取平均值
        avg = Counter()
        n = len(prev_data)
        for day_data in prev_data:
            for kw, cnt in day_data.items():
                avg[kw] += cnt
        for kw in avg:
            avg[kw] = round(avg[kw] / n)
        return avg

    def _compute_changes(
        self, current: Counter, previous: Counter
    ) -> list[dict]:
        """计算环比变化"""
        changes = []
        for kw, curr in current.most_common(50):
            prev = previous.get(kw, 0)
            if prev > 0:
                pct = round((curr - prev) / prev * 100, 1)
            else:
                pct = 100 if curr > 0 else 0
            changes.append({
                "keyword": kw,
                "current": curr,
                "previous_avg": prev,
                "change_pct": pct,
            })
        # 按变化率排序
        changes.sort(key=lambda x: x["change_pct"], reverse=True)
        return changes

    def _detect_surges(self, changes: list[dict]) -> list[dict]:
        """识别热度飙升 > 阈值的关键词"""
        return [
            c for c in changes
            if c["change_pct"] >= self.surge_threshold and c["current"] >= 3
        ]

    def _ai_analyze_causes(
        self, tagged: list[dict], changes: list[dict],
        surges: list[dict], report_date: date
    ) -> str:
        """调用 AI 分析热度变化的原因"""
        sample_content = []
        for r in tagged[:30]:
            if r.get("matched_keywords"):
                sample_content.append({
                    "title": r.get("title", "")[:100],
                    "content_snippet": r.get("content", "")[:200],
                    "platform": r.get("platform", ""),
                })

        prompt = f"""
你是中国市场极地旅游分析专家。分析以下南极相关数据，用中文简要解释热度变化原因（150字以内）。

日期: {report_date}
飙升关键词: {json.dumps([s["keyword"] for s in surges], ensure_ascii=False)}
热度变化 TOP5: {json.dumps(changes[:5], ensure_ascii=False)}
样本内容: {json.dumps(sample_content[:10], ensure_ascii=False)}

请分析:
1. 热度变化的主要原因
2. 是否受季节/节假日/热点事件影响
3. 一句话总结今日市场特征
"""
        try:
            from agents.llm_client import chat
            return chat(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=300,
            ).strip()
        except Exception as e:
            print(f"  ⚠️ AI 分析调用失败: {e}")
            return f"热度变化可能受季节性长线旅游规划窗口影响。详细分析请查看数据报告。"

    def _generate_alerts(
        self, changes: list[dict], surges: list[dict]
    ) -> list[str]:
        """生成告警信息"""
        alerts = []
        for s in surges:
            alerts.append(
                f"🔥 关键词「{s['keyword']}」热度飙升 +{s['change_pct']}%"
            )
        return alerts

    def _save_results(self, result: dict, report_date: date) -> None:
        """保存中间结果供后续 Agent 使用"""
        os.makedirs("data/processed", exist_ok=True)
        # 保存关键词计数
        with open(f"data/processed/keyword_counts_{report_date}.json", "w", encoding="utf-8") as f:
            json.dump(result["keyword_breakdown"], f, ensure_ascii=False)
        # 保存完整结果
        with open(f"data/processed/keyword_radar_{report_date}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
