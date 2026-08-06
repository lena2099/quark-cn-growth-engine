"""
实时数据看板 — Streamlit 应用
提供线索Pipeline、竞品动态、KPI趋势的实时可视化
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Quark CN Growth Engine",
    page_icon="🐧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════
# 侧边栏 — 导航
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://www.quarkexpeditions.cn/favicon.ico", width=48)
    st.title("Quark CN Growth")
    st.caption("中国市场增长引擎 v1.0")

    st.divider()
    page = st.radio(
        "导航",
        [
            "📊 总览仪表盘",
            "🎯 渠道Pipeline",
            "👥 联系人线索",
            "🔍 竞品动态",
            "📈 KPI 趋势",
            "⚙️ 系统状态",
        ],
    )

    st.divider()
    st.metric("引擎运行时间", "23h 45m")
    st.metric("今日线索", "—", delta="+12")
    st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ═══════════════════════════════════════════════════════
# 总览仪表盘
# ═══════════════════════════════════════════════════════
if page == "📊 总览仪表盘":
    st.title("📊 总览仪表盘")

    # KPI 卡片行
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("累计线索", "—", delta="+248 本月")
    with col2:
        st.metric("签约伙伴", "—", delta="+5 本月")
    with col3:
        st.metric("高意向线索", "—", delta="+18 本周")
    with col4:
        st.metric("预订转化", "—", delta="+32")
    with col5:
        st.metric("品牌声量指数", "—", delta="+156%")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🔥 热门线索（评分 ≥ 70）")
        st.info("实时热门线索将在此展示。启动采集引擎后自动填充。")
        # 示例数据展示结构
        st.dataframe(
            pd.DataFrame({
                "评分": [85, 82, 78, 75, 72],
                "公司": ["待采集", "待采集", "待采集", "待采集", "待采集"],
                "联系人": ["—", "—", "—", "—", "—"],
                "状态": ["新发现", "新发现", "待触达", "待触达", "已触达"],
            }),
            use_container_width=True,
        )

    with col_right:
        st.subheader("📅 最近竞品动态")
        st.info("竞品动态将在监控引擎运行后自动填充。")
        events = [
            {"时间": "2h前", "竞品": "庞洛", "事件": "新产品发布", "紧迫度": "🔴"},
            {"时间": "5h前", "竞品": "众信旅游", "事件": "南极包船公告", "紧迫度": "🟡"},
            {"时间": "1d前", "竞品": "66度", "事件": "新船命名", "紧迫度": "🟢"},
        ]
        for e in events:
            st.write(f"{e['紧迫度']} [{e['时间']}] **{e['竞品']}**: {e['事件']}")

    st.divider()
    st.subheader("📈 线索增长趋势（最近30天）")
    st.info("图表将在数据累积后自动渲染。部署后可见真实趋势。")

# ═══════════════════════════════════════════════════════
# 渠道Pipeline
# ═══════════════════════════════════════════════════════
elif page == "🎯 渠道Pipeline":
    st.title("🎯 渠道 Pipeline")

    # Pipeline 阶段
    stages = ["🔍 发现", "📋 评估中", "🤝 洽谈中", "✍️ 签约", "✅ 活跃"]
    cols = st.columns(len(stages))

    for i, (col, stage) in enumerate(zip(cols, stages)):
        with col:
            st.subheader(stage)
            st.metric("数量", f"{i * 3 + 2}")
            st.progress((i + 1) / len(stages))

    st.divider()
    st.subheader("Tier 1 战略伙伴跟进状态")

    tier1_data = pd.DataFrame({
        "伙伴": ["众信旅游集团", "鸿鹄逸游", "极至旅行", "极之美", "北京船客"],
        "Tier": ["P0", "P0", "P0", "P1", "P1"],
        "状态": ["洽谈中", "待触达", "待触达", "待触达", "待触达"],
        "上次联系": ["—", "—", "—", "—", "—"],
        "下一步": [
            "差异化提案提交",
            "携程渠道对接会",
            "专业对话会",
            "北极格陵兰方案",
            "包船提案",
        ],
    })
    st.dataframe(tier1_data, use_container_width=True)

# ═══════════════════════════════════════════════════════
# 联系人线索
# ═══════════════════════════════════════════════════════
elif page == "👥 联系人线索":
    st.title("👥 联系人线索库")

    tab1, tab2, tab3 = st.tabs(["领英线索", "脉脉线索", "全部联系人"])

    with tab1:
        st.subheader("领英公开联系人")
        st.info("启动 LinkedIn Connector 后将自动填充。目标：20家 × 5角色 = 100+联系人")

    with tab2:
        st.subheader("脉脉公开名片")
        st.info("启动 Maimai Connector 后将自动填充。")

    with tab3:
        st.subheader("联系人总览")
        st.info("所有来源联系人汇总视图。")

# ═══════════════════════════════════════════════════════
# 竞品动态
# ═══════════════════════════════════════════════════════
elif page == "🔍 竞品动态":
    st.title("🔍 竞品动态监控")

    st.subheader("竞品品牌声量对比")
    brands = ["庞洛", "银海", "夸克(Quark)", "66度", "海达路德", "Antarctica21"]
    st.info("微信指数/百度指数对比图表（需接入数据API）")

    st.divider()
    st.subheader("⚠️ 高优先级预警")
    st.warning("配置竞品追踪关键词后，高紧迫度事件将在此实时显示。")

# ═══════════════════════════════════════════════════════
# KPI 趋势
# ═══════════════════════════════════════════════════════
elif page == "📈 KPI 趋势":
    st.title("📈 100天 KPI 进度")

    st.subheader("Phase 进度")
    phases = {
        "Phase 1: 基础建设 (D1-25)": 0,
        "Phase 2: 渠道激活 (D26-50)": 0,
        "Phase 3: 市场引爆 (D51-75)": 0,
        "Phase 4: 闭环转化 (D76-100)": 0,
    }
    for phase, pct in phases.items():
        st.progress(pct, text=phase)

    st.divider()
    st.subheader("核心KPI追踪")

    kpi_data = pd.DataFrame({
        "KPI": [
            "签约B2B伙伴", "渠道培训认证人数", "小红书粉丝",
            "公众号关注", "渠道线索总量", "高意向线索",
            "预订量(26-27季)", "包船航次",
        ],
        "当前": ["—"] * 8,
        "D25目标": [5, 20, "1,000", "1,000", 50, 10, 20, 0],
        "D50目标": [15, 60, "3,000", "2,500", 200, 40, 60, 1],
        "D75目标": [25, 100, "8,000", "5,000", 500, 100, 120, 2],
        "D100目标": [30, 150, "15,000", "8,000", 800, 180, 200, 3],
    })
    st.dataframe(kpi_data, use_container_width=True)

# ═══════════════════════════════════════════════════════
# 系统状态
# ═══════════════════════════════════════════════════════
elif page == "⚙️ 系统状态":
    st.title("⚙️ 系统状态")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("调度器状态")
        st.metric("状态", "待启动")
        st.metric("已注册任务", "10")

    with col2:
        st.subheader("数据库状态")
        st.metric("PostgreSQL", "待连接")
        st.metric("Redis", "待连接")

    st.divider()
    st.subheader("任务执行日志")
    st.code("""
[2026-08-07 06:00:01] Channel Discovery: 扫描完成，发现 0 条新线索
[2026-08-07 05:00:01] LinkedIn Scan: 扫描完成，发现 0 条新联系人
[2026-08-07 00:00:01] Competitor Monitor: 扫描完成，0 条动态
[INFO] 引擎初始化完成，等待首次调度触发...
    """)

    st.divider()
    st.caption("Quark CN Growth Engine v1.0 | 部署日期: 2026-08-07")
