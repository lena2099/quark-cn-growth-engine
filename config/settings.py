"""
全局配置 — 关键词库 / 竞品 / 平台 / 品牌
所有可配置参数集中管理，方便营销团队自行调整
"""

# ═══════════════════════════════════════════════
# 一、关键词库 — 三级分类
# ═══════════════════════════════════════════════

KEYWORD_LIBRARY = {
    # 一级：产品词 (核心产品相关的直接搜索)
    "product": {
        "weight": 1.0,
        "keywords": [
            "南极旅游", "南极旅行", "南极邮轮", "南极探险",
            "南极游轮", "南极多少钱", "南极路线", "南极攻略",
            "南极船票", "南极行程", "南极旅游攻略", "去南极",
            "南极旅行团", "南极自由行", "南极船公司",
        ]
    },
    # 二级：需求词 (反映深层需求和人群画像)
    "demand": {
        "weight": 0.8,
        "keywords": [
            "人生清单", "人生必去", "50岁旅行", "退休旅行",
            "高端旅行", "奢华旅行", "环球旅行", "摄影旅行",
            "亲子旅行", "极地旅行", "豪华邮轮", "深度旅行",
            "小众旅行地", "一生必去", "终极旅行",
        ]
    },
    # 三级：情绪词 (反映购买阶段和情绪状态)
    "emotion": {
        "weight": 0.6,
        "keywords": [
            "想去", "梦想", "计划", "什么时候去",
            "值得吗", "费用", "安全吗", "好玩吗",
            "推荐吗", "怎么选", "哪家好", "值不值",
            "性价比", "太贵了", "便宜吗", "价格",
            "适合吗", "需要什么准备", "签证", "装备",
        ]
    },
    # 竞品关联词 (用户搜索竞品 → 可能是我们的潜在客户)
    "competitor_adjacent": {
        "weight": 0.5,
        "keywords": [
            "海达路德", "庞洛", "Aurora Expeditions",
            "凯撒南极", "携程南极", "同程南极",
            "南极跟团", "南极华人团",
        ]
    },
}

# ═══════════════════════════════════════════════
# 二、竞争品牌监控列表
# ═══════════════════════════════════════════════

COMPETITOR_BRANDS = [
    {
        "name": "夸克探险",
        "name_en": "Quark Expeditions",
        "is_own": True,
        "aliases": ["夸克", "Quark", "夸克游轮", "夸克邮轮"],
    },
    {
        "name": "海达路德",
        "name_en": "Hurtigruten",
        "is_own": False,
        "aliases": ["海达路德游轮", "Hurtigruten", "HX"],
    },
    {
        "name": "庞洛",
        "name_en": "Ponant",
        "is_own": False,
        "aliases": ["庞洛邮轮", "Ponant", "庞洛游轮"],
    },
    {
        "name": "Aurora Expeditions",
        "name_en": "Aurora Expeditions",
        "is_own": False,
        "aliases": ["Aurora", "欧若拉探险"],
    },
    {
        "name": "银海邮轮",
        "name_en": "Silversea",
        "is_own": False,
        "aliases": ["银海", "Silversea", "银海游轮"],
    },
    {
        "name": "Lindblad Expeditions",
        "name_en": "Lindblad Expeditions",
        "is_own": False,
        "aliases": ["Lindblad", "国家地理邮轮"],
    },
]

# ═══════════════════════════════════════════════
# 三、监控平台配置
# ═══════════════════════════════════════════════

PLATFORMS = {
    "xiaohongshu": {
        "name": "小红书",
        "enabled": True,
        "metrics": ["search_trend", "note_count", "save_count", "comment_sentiment", "top_creators"],
        "search_sources": ["note", "topic", "user"],
    },
    "douyin": {
        "name": "抖音",
        "enabled": True,
        "metrics": ["video_views", "comment_keywords", "user_questions", "engagement_rate"],
        "search_sources": ["video", "hashtag", "user"],
    },
    "wechat_article": {
        "name": "微信公众号",
        "enabled": True,
        "metrics": ["article_count", "read_trend", "travel_agency_content", "publish_frequency"],
        "search_sources": ["article", "account"],
    },
    "wechat_video": {
        "name": "视频号",
        "enabled": True,
        "metrics": ["brand_accounts", "luxury_travel_kol", "private_domain_spread"],
        "search_sources": ["video", "account"],
    },
}

# ═══════════════════════════════════════════════
# 四、AI 分析模型配置
# ═══════════════════════════════════════════════

AI_CONFIG = {
    # DeepSeek API — 兼容 OpenAI SDK, 性价比极高
    # deepseek-chat: 通用对话模型 (≈ GPT-4o 级别, 成本约 1/10)
    # deepseek-reasoner: 深度推理模型 (复杂分析场景按需切换)
    "provider": "deepseek",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "temperature": 0.3,
    "max_tokens": 2048,
    "intent_analysis": {
        "model": "deepseek-chat",
        "temperature": 0.2,
        "prompt_template": "intent_analyzer_v1",
    },
    "report_generation": {
        "temperature": 0.4,
        "max_tokens": 4096,
    },
}

# ═══════════════════════════════════════════════
# 五、用户画像标签
# ═══════════════════════════════════════════════

USER_PROFILE_LABELS = {
    "age_group": ["25-35", "35-45", "45-55", "55-65", "65+"],
    "gender": ["男性", "女性", "未知"],
    "income_level": ["高净值", "中产偏高", "中产", "价格敏感"],
    "travel_type": ["奢华旅行者", "摄影爱好者", "冒险家", "亲子家庭", "退休旅者"],
    "purchase_stage": ["认知期", "考虑期", "比较期", "决策期", "复购期"],
    "intent_level": ["强购买信号", "中等兴趣", "观望", "信息收集"],
}

# ═══════════════════════════════════════════════
# 六、报告配置
# ═══════════════════════════════════════════════

REPORT_CONFIG = {
    "title": "Quark Expeditions 中国市场日报",
    "subtitle": "Polar Market Intelligence Agent",
    "sections": [
        "今日市场概览",
        "关键词雷达",
        "社媒热榜",
        "用户意图洞察",
        "品牌声量监测",
        "竞品动态",
        "市场机会与建议",
    ],
    "output_formats": ["markdown", "json", "html"],
    "comparison_window_days": 7,  # 对比过去 N 天的变化
}

# ═══════════════════════════════════════════════
# 七、告警阈值
# ═══════════════════════════════════════════════

ALERT_THRESHOLDS = {
    "keyword_surge_pct": 30,         # 关键词热度飙升 30% 触发告警
    "competitor_surge_pct": 25,      # 竞品声量增长 25% 触发告警
    "own_brand_share_drop": 2.0,     # 夸克声量占比下降 2 个百分点触发告警
    "negative_sentiment_pct": 20,    # 负面情绪占比超 20% 触发告警
    "high_intent_user_count": 5,     # 单个平台强购买意图用户超过 5 人高亮
}
