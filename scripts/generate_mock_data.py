"""
模拟数据生成器 — 用于 MVP 阶段流程验证
当 data/raw/ 中没有实际数据时，生成逼真的模拟数据
"""

import random
from datetime import date, timedelta

# 真实的中国南极旅游关键词池
KEYWORDS = [
    "南极旅游", "南极旅行", "南极邮轮", "南极探险", "南极游轮",
    "南极多少钱", "南极路线", "南极攻略", "南极旅行团", "去南极",
    "南极旅游攻略", "南极船票", "南极自由行",
]

EMOTION_WORDS = ["想去", "梦想", "计划", "值得吗", "费用", "安全吗", "推荐吗", "哪家好"]

PLATFORMS = [
    {"key": "xiaohongshu", "name": "小红书"},
    {"key": "xiaohongshu", "name": "小红书"},
    {"key": "xiaohongshu", "name": "小红书"},
    {"key": "xiaohongshu", "name": "小红书"},
    {"key": "douyin", "name": "抖音"},
    {"key": "douyin", "name": "抖音"},
    {"key": "douyin", "name": "抖音"},
    {"key": "wechat_article", "name": "微信公众号"},
    {"key": "wechat_video", "name": "视频号"},
]

AUTHORS = [
    "旅行者小美", "极地探险老王", "环球旅人Lena", "摄影师阿杰",
    "50岁开始旅行", "高端旅行规划师", "南极归来的Lucy", "行走的地图",
    "退休生活指南", "亲子旅行家", "奢华旅行日记", "冒险家David",
    "深度旅行控", "极地邮轮专家", "环球梦想家",
]

TITLES = [
    "南极旅游全攻略｜2026年最新版超详细",
    "去南极要花多少钱？我的真实账单公开",
    "50岁终于完成了人生清单第一站：南极！",
    "南极邮轮怎么选？夸克vs海达路德vs庞洛对比",
    "南极旅行值不值得？回来后的真实感受",
    "退休后第一站：南极！比想象中震撼100倍",
    "南极探险｜一个人去南极的30天",
    "南极拍摄攻略｜摄影爱好者必看",
    "南极旅行避坑指南！这些千万别踩",
    "带着妈妈去南极｜亲子旅行天花板",
    "南极旅游2026年最新价格整理",
    "南极旅行路线推荐｜第一次去选这条",
    "为什么说南极是一生必去的地方",
    "南极探险船公司排行榜｜真实体验分享",
    "花了20万去南极，是智商税吗？",
    "南极旅游安全吗？你需要知道这些",
    "退休旅行计划｜南极是我的第一站",
    "南极旅行装备清单｜超全整理",
    "南极邮轮上的生活｜一天是怎么过的",
    "南极旅行签证攻略｜一文说清楚",
    "南极旅行｜你问我答 省钱版",
    "奢华旅行推荐｜南极邮轮顶配体验",
    "环球旅行第7站：南极洲🇦🇶",
    "南极回来一个月，人还在震撼中",
    "南极旅行｜不同船公司体验大对比",
    "2026南极旅行团｜华人包船信息汇总",
    "南极跟团还是自由行？过来人告诉你",
    "庞洛邮轮南极体验｜奢华还是溢价？",
    "海达路德南极探险｜挪威人的极地基因",
    "南极旅行到底多少预算才够",
]

CONTENTS = [
    "一直想去南极，看了很多攻略终于下定决心。请问大家推荐哪个船公司？预算20万左右，希望有中文服务。",
    "50岁以后一定要去一次南极，希望明年完成这个梦想。有没有退休的朋友一起组队？",
    "南极20万是不是智商税？朋友说花这么多钱就看冰山和企鹅，让我犹豫了。去过的人说说值不值？",
    "对比了夸克、海达路德、庞洛这三家，感觉夸克的探险属性更强，海达路德偏舒适，庞洛偏奢华。大家觉得呢？",
    "刚从南极回来！真的太震撼了！强烈推荐夸克探险，船上的探险队员非常专业，登陆次数也比其他船多。",
    "请问去南极需要什么签证？在阿根廷上船需要阿根廷签证吗？有没有最近去的朋友分享一下？",
    "退休后想完成环球旅行的梦想，南极是第一站。请问12月去好还是1月去好？",
    "南极旅行安全吗？会不会遇到极端天气？一个人去会不会很危险？",
    "带10岁的孩子去南极合适吗？有没有亲子友好的船公司推荐？",
    "南极旅行装备清单分享：从保暖内衣到防水裤，一篇文章讲清楚所有你需要准备的！",
    "南极邮轮选船攻略：不同吨位、不同设施、不同登陆体验的详细对比。",
    "南极旅行的费用构成解析：船票+机票+签证+装备+小费，一次性算清楚。",
    "看了极地旅行的纪录片被种草了！请问第一次去南极推荐什么路线？经典半岛线还是三岛线？",
    "南极旅行回来，最大的感触不是风景有多美，而是对自然的敬畏。每个人都应该去一次。",
    "南极跟团好还是自由行好？其实南极几乎没有真正的自由行，都是跟船公司。关键在于选对船！",
    "2026年南极旅行的价格涨了好多，比2024年贵了30%。还要不要现在去？还是再等等？",
    "南极旅行｜海达路德被收购后改名叫HX了，新船的确很现代，但总觉得少了极地探险的味道。",
    "庞洛邮轮的南极体验分享：确实是奢华级别的享受，但价格也是天花板级别的。适合预算充足的朋友。",
    "南极旅行｜我为什么选择了夸克探险而不是其他品牌？核心原因是他们的探险精神和专业度。",
    "南极旅行｜评论区说说你们去南极花了多少钱？我做个统计给大家参考。船票8-15万不等，丰俭由人。",
]

COMMENTS_POOLS = [
    ["多少钱？", "同问价格", "求攻略🙏", "收藏了！"],
    ["怎么报名？", "有联系方式吗", "求推荐靠谱旅行社", "mark"],
    ["太美了！一定要去", "梦想中的旅行", "羡慕", "我也想去😭"],
    ["安全吗？", "会不会很冷", "需要什么准备？", "一个人去方便吗？"],
    ["性价比怎么样？", "值得去吗？", "求真实评价", "会不会是智商税"],
    ["请问适合带老人吗？", "60岁能去吗？", "有年龄限制吗？"],
    ["签证好办吗？", "需要什么签证？", "从哪个国家出发？"],
    ["对比一下其他家", "夸克好还是海达路德好？", "庞洛怎么样？"],
    ["价格有点贵啊", "有没有便宜点的方案？", "预算有限怎么办"],
    ["已经报名了！明年1月出发", "我也订了", "有一起的吗？"],
]


def generate_mock_data(report_date: date, num_records: int = 80) -> list[dict]:
    """
    生成模拟的社媒数据，格式与人工导入 CSV 一致:
    date, platform, keyword, title, link, likes, comments, saves, author, content, comments_content
    """
    random.seed(report_date.toordinal())  # 同一天生成的数据一致

    records = []
    for i in range(num_records):
        # 概率分布: 20% 产品词, 50% 产品词+需求词, 25% 产品词+情绪词, 5% 竞品
        roll = random.random()
        kw = random.choice(KEYWORDS)

        if roll < 0.05:
            # 竞品相关内容
            extra_words = random.choice(["海达路德", "庞洛", "Aurora", "银海邮轮"])
            title = f"南极旅行｜{extra_words}体验分享"
            content = f"对比了夸克和{extra_words}，各有特色。{random.choice(CONTENTS)}"
        elif roll < 0.25:
            title = random.choice(TITLES)
            extra = random.choice(EMOTION_WORDS)
            content = f"{random.choice(CONTENTS)} {extra}"
        elif roll < 0.50:
            title = random.choice(TITLES)
            content = f"{random.choice(CONTENTS)} 人生清单 退休旅行"
        else:
            title = random.choice(TITLES)
            content = random.choice(CONTENTS)

        platform = random.choice(PLATFORMS)
        # 小红书数据一般互动量高于其他平台
        is_xhs = platform["key"] == "xiaohongshu"
        likes = random.randint(20, 500) * (3 if is_xhs else 1)
        comments = random.randint(3, 80) * (2 if is_xhs else 1)
        saves = random.randint(5, 200) * (2 if is_xhs else 1)

        # 随机选一组合并的评论
        comment_pool = random.choice(COMMENTS_POOLS)
        comments_content = " | ".join(random.sample(comment_pool, random.randint(1, len(comment_pool))))

        records.append({
            "date": str(report_date),
            "platform": platform["key"],
            "platform_name": platform["name"],
            "keyword": kw,
            "title": title,
            "link": f"https://{platform['key']}.com/post/{random.randint(10000, 99999)}",
            "likes": str(likes),
            "comments": str(comments),
            "saves": str(saves),
            "author": random.choice(AUTHORS),
            "content": content,
            "comments_content": comments_content,
        })

    # 保存为 JSON (供 main.py 读取)
    import os, json
    os.makedirs("data/raw", exist_ok=True)
    output_path = f"data/raw/{report_date}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"  📊 已生成 {len(records)} 条模拟数据 → {output_path}")
    return records


# 可直接运行测试
if __name__ == "__main__":
    data = generate_mock_data(date.today() - timedelta(days=1))
    print(f"\n示例数据 (第一条):")
    print(json.dumps(data[0], ensure_ascii=False, indent=2))
