"""
去重引擎
确保线索和联系人不重复入库
"""
import hashlib
import logging
from typing import List, Dict, Set

logger = logging.getLogger("quark.processors.dedup")


class DedupEngine:
    """多级去重策略"""

    def __init__(self):
        self._seen_lead_ids: Set[str] = set()
        self._seen_contact_ids: Set[str] = set()
        self._seen_company_names: Set[str] = set()

    async def filter_new(self, leads: List[Dict]) -> List[Dict]:
        """
        过滤新增线索

        去重策略：
        1. 基于 lead.id (MD5 hash) 精确去重
        2. 基于公司名模糊去重（相似度 > 80%）
        3. 基于 URL 去重
        """
        new_leads = []

        for lead in leads:
            lead_id = lead.get("id", "")

            # 1. ID 精确去重
            if lead_id in self._seen_lead_ids:
                logger.debug(f"Duplicate lead (ID): {lead_id}")
                continue

            # 2. 公司名去重
            companies = lead.get("extracted_companies", [])
            if companies:
                company = companies[0]
                if self._is_company_duplicate(company):
                    logger.debug(f"Duplicate company: {company}")
                    continue

            # 3. URL 去重
            url = lead.get("url", "")
            url_hash = hashlib.md5(url.encode()).hexdigest() if url else ""
            if url_hash and url_hash in self._seen_lead_ids:
                logger.debug(f"Duplicate lead (URL): {url}")
                continue

            # 新线索
            self._seen_lead_ids.add(lead_id)
            if url_hash:
                self._seen_lead_ids.add(url_hash)
            if companies:
                self._seen_company_names.add(companies[0].lower())

            new_leads.append(lead)

        return new_leads

    async def filter_new_contacts(self, contacts: List[Dict]) -> List[Dict]:
        """过滤新增联系人"""
        new_contacts = []

        for contact in contacts:
            contact_id = contact.get("id", "")

            if contact_id in self._seen_contact_ids:
                continue

            # 姓名+公司+职位联合去重
            composite_key = (
                contact.get("name", "")
                + contact.get("company_name", "")
                + contact.get("title", "")
            )
            composite_hash = hashlib.md5(composite_key.encode()).hexdigest()
            if composite_hash in self._seen_contact_ids:
                continue

            self._seen_contact_ids.add(contact_id)
            self._seen_contact_ids.add(composite_hash)
            new_contacts.append(contact)

        return new_contacts

    def _is_company_duplicate(self, company_name: str) -> bool:
        """模糊公司名去重"""
        name_lower = company_name.lower().strip()

        if name_lower in self._seen_company_names:
            return True

        # 简易相似度检查：核心词匹配
        core_words = self._extract_core_words(name_lower)
        for seen in self._seen_company_names:
            seen_words = self._extract_core_words(seen)
            common = core_words & seen_words
            if len(common) >= 2 and len(common) / max(len(core_words), len(seen_words)) > 0.6:
                return True

        return False

    def _extract_core_words(self, name: str) -> Set[str]:
        """提取公司名核心词（去除通用后缀）"""
        generic_suffixes = {"有限", "公司", "集团", "旅行社", "旅游", "旅行", "国际"}
        words = set()
        for word in name.replace(",", " ").replace("，", " ").split():
            word = word.strip()
            if word and word not in generic_suffixes and len(word) >= 2:
                words.add(word)
        return words

    def reset(self):
        """重置去重状态（用于测试）"""
        self._seen_lead_ids.clear()
        self._seen_contact_ids.clear()
        self._seen_company_names.clear()
