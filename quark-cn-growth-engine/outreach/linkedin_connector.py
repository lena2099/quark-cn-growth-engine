"""
LinkedIn 联系人自动采集器 (Workflow 2 - Part A)
从领英公开页面提取目标公司关键决策人信息

合规要求：
- 仅访问公开可索引的个人资料
- 不绕过任何反爬措施
- 不使用虚假/非本人账号
- 遵守 robots.txt 和频率限制
- 符合 GDPR / 《个人信息保护法》
"""
import asyncio
import hashlib
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger("quark.collectors.linkedin")


class LinkedInConnector:
    """
    领英公开信息采集器

    采集策略：
    1. 通过 Google 搜索 site:linkedin.com/in/ "{company}" "{role}" 获取公开结果
    2. 解析搜索结果片段提取姓名/职位
    3. 不直接爬取领英页面（遵守反爬政策）

    或使用：
    - LinkedIn Sales Navigator API (需付费订阅)
    - 第三方合规数据提供商 (如 ZoomInfo, Apollo.io)
    """

    def __init__(self, config: dict):
        self.config = config
        self.outreach_cfg = config["outreach"]["linkedin"]
        self.daily_limit = self.outreach_cfg["daily_connection_limit"]
        self._daily_count = 0

        # 目标公司列表从 targets.yaml 加载
        self.targets = self._load_targets()

    def _load_targets(self) -> List[Dict]:
        """加载目标合作伙伴清单"""
        import yaml
        from pathlib import Path

        targets_path = Path(__file__).parent.parent / "config" / "targets.yaml"
        with open(targets_path) as f:
            data = yaml.safe_load(f)

        return data.get("partners", [])

    async def scan_targets(self) -> List[Dict]:
        """
        主扫描入口：为每个目标公司搜索关键联系人

        返回格式:
        [
            {
                "id": "unique_contact_id",
                "source": "linkedin",
                "company_id": "ZS-001",
                "company_name": "众信旅游集团",
                "name": "张三",
                "name_en": "Zhang San",
                "title": "极地邮轮中心负责人",
                "linkedin_url": "https://linkedin.com/in/...",
                "profile_snippet": "...",
                "public_email": null,
                "discovered_at": "2026-08-07T06:00:00",
                "confidence": 0.85,
            }
        ]
        """
        contacts = []

        for target in self.targets:
            if self._daily_count >= self.daily_limit:
                logger.warning("Daily LinkedIn limit reached.")
                break

            company_name = target["name"]
            company_id = target["id"]
            search_roles = target.get("search_roles", [])

            for role in search_roles:
                if self._daily_count >= self.daily_limit:
                    break

                try:
                    result = await self._search_contact(company_name, role, company_id)
                    if result:
                        contacts.append(result)
                        self._daily_count += 1
                except Exception as e:
                    logger.error(f"LinkedIn search failed for {company_name}/{role}: {e}")

                await asyncio.sleep(3)  # 频率控制

        logger.info(f"LinkedIn scan: {len(contacts)} contacts found (daily count: {self._daily_count})")
        return contacts

    async def _search_contact(
        self, company: str, role: str, company_id: str
    ) -> Optional[Dict]:
        """
        搜索模式:

        方案A：Google 公开搜索（适合初期MVP）
          site:linkedin.com/in "{company}" "{role}"
          → 解析搜索结果片段

        方案B：LinkedIn Sales Navigator API（推荐生产环境）
          POST /v2/search
          → companies: [{name}], title: [{role}]

        方案C：第三方数据平台（如 Apollo.io, Lusha）
          → API 直接返回结构化数据

        以下实现方案A作为起始点
        """
        # 构造搜索查询
        query = f'site:linkedin.com/in/ "{company}" "{role}"'

        # TODO: 实际部署时使用 Google Custom Search API
        # from googleapiclient.discovery import build
        # service = build("customsearch", "v1", developerKey=API_KEY)
        # result = service.cse().list(q=query, cx=SEARCH_ENGINE_ID).execute()

        # 此处为结构示例
        logger.debug(f"LinkedIn search query: {query}")

        # 模拟解析搜索结果片段
        # 实际部署时替换为真实API响应解析
        contact = self._parse_search_result_snippet(
            company=company,
            role=role,
            company_id=company_id,
            snippet="",  # 真实部署时从搜索结果获取
            url="",       # 真实部署时从搜索结果获取
        )

        return contact

    def _parse_search_result_snippet(
        self,
        company: str,
        role: str,
        company_id: str,
        snippet: str,
        url: str,
    ) -> Optional[Dict]:
        """
        解析 Google 搜索结果片段

        示例片段:
        "张三 - 极地邮轮中心负责人 - 众信旅游集团 | LinkedIn"
        解析出: name="张三", title="极地邮轮中心负责人"
        """
        if not snippet:
            return None

        # 提取姓名（LinkedIn片段通常以姓名开头）
        name_match = re.match(r"^([\u4e00-\u9fff·]{2,4})", snippet)
        name = name_match.group(1) if name_match else ""

        # 提取职位
        title_pattern = r"[-–—]\s*([^|•-]+?)\s*[-–—]"
        title_match = re.search(title_pattern, snippet)
        title = title_match.group(1).strip() if title_match else role

        # 提取 LinkedIn URL
        linkedin_url = ""
        if "linkedin.com/in/" in url:
            match = re.search(r"(https?://[^\s&]+linkedin\.com/in/[^\s&]+)", url)
            linkedin_url = match.group(1) if match else url

        # 提取可能的邮箱（片段中偶尔出现）
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", snippet)
        public_email = email_match.group(0) if email_match else None

        contact_id = hashlib.md5(
            f"li:{company}:{name}:{title}".encode()
        ).hexdigest()[:16]

        return {
            "id": contact_id,
            "source": "linkedin",
            "company_id": company_id,
            "company_name": company,
            "name": name,
            "name_en": "",
            "title": title,
            "linkedin_url": linkedin_url,
            "profile_snippet": snippet,
            "public_email": public_email,
            "discovered_at": datetime.now().isoformat(),
            "confidence": 0.7 if name else 0.3,
        }

    async def send_connection_request(
        self, contact: Dict, note: str = None
    ) -> bool:
        """
        发送领英连接邀请（需手动确认或使用API）

        注意：自动化连接请求受领英平台政策严格限制
        建议：先采集联系人信息，再由团队成员手动发送个性化邀请
        """
        if self._daily_count >= self.daily_limit:
            return False

        # TODO: 实际部署时评估合规方案
        # 选项1: LinkedIn API (需申请 Partnership)
        # 选项2: Sales Navigator InMail
        # 选项3: 团队成员手动操作（推荐初期）
        logger.info(
            f"Connection request prepared for: {contact['name']} "
            f"({contact['company_name']})"
        )
        self._daily_count += 1
        return True
