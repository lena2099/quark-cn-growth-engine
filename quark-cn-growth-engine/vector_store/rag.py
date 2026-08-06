"""
pgvector 向量数据库集成 — 客户语义检索 (RAG)

对应 Polar Growth OS 数据架构：
  PostgreSQL + pgvector → 客户向量嵌入 → 语义检索 → Agent 上下文增强

用途：
  1. 客户相似度搜索 — "找到和已购客户相似的高意向潜客"
  2. 异议语义检索 — 销售输入客户问题 → 检索最相关的历史成功回应
  3. 内容推荐 — 基于客户兴趣向量推荐最匹配的内容
"""
import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("quark.vector_store")


# ═══════════════════════════════════════════════════════════
# 向量嵌入抽象层
# ═══════════════════════════════════════════════════════════

class EmbeddingClient:
    """
    向量嵌入客户端

    支持：
    - OpenAI text-embedding-3-small (推荐，1536维)
    - 本地模型 fallback (sentence-transformers)
    """

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.dimensions = 1536 if "3-small" in model else 3072

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        将文本转换为向量

        实际部署：
          from openai import AsyncClient
          client = AsyncClient()
          resp = await client.embeddings.create(model=self.model, input=texts)
          return [d.embedding for d in resp.data]

        当前为模拟实现。
        """
        # 模拟：用 hash 生成确定性假向量（仅演示架构）
        mock_embeddings = []
        for text in texts:
            h = hashlib.sha256(text.encode()).digest()
            # 将 32 字节 hash 展开为 1536 维（通过重复+变换）
            vec = []
            for i in range(self.dimensions):
                byte_val = h[i % 32]
                # 简单的伪随机分布
                vec.append((byte_val / 255.0) * 2 - 1)
            mock_embeddings.append(vec)
        return mock_embeddings

    async def embed_single(self, text: str) -> List[float]:
        embeddings = await self.embed([text])
        return embeddings[0]


# ═══════════════════════════════════════════════════════════
# 向量存储
# ═══════════════════════════════════════════════════════════

@dataclass
class CustomerVector:
    """客户向量记录"""
    customer_id: str
    embedding: List[float]
    metadata: Dict
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SearchResult:
    """检索结果"""
    customer_id: str
    similarity: float
    metadata: Dict


class VectorStore:
    """
    向量存储 (pgvector 模拟)

    实际部署 SQL：
      CREATE EXTENSION vector;
      CREATE TABLE customer_vectors (
        id SERIAL PRIMARY KEY,
        customer_id TEXT UNIQUE,
        embedding vector(1536),
        metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW()
      );
      CREATE INDEX ON customer_vectors USING ivfflat (embedding vector_cosine_ops);

    查询示例：
      SELECT customer_id, 1 - (embedding <=> $query_vector) AS similarity, metadata
      FROM customer_vectors
      ORDER BY embedding <=> $query_vector
      LIMIT 10;
    """

    def __init__(self):
        self._store: Dict[str, CustomerVector] = {}
        self._embedder = EmbeddingClient()

    async def insert(self, customer_id: str, text: str, metadata: Dict):
        """插入客户向量"""
        embedding = await self._embedder.embed_single(text)
        self._store[customer_id] = CustomerVector(
            customer_id=customer_id,
            embedding=embedding,
            metadata=metadata,
        )

    async def search_similar(
        self, query_text: str, top_k: int = 10
    ) -> List[SearchResult]:
        """
        语义搜索：找与查询最相似的客户

        应用场景：
        - "找到和已购南极客户相似的高意向潜客"
        - "这个新线索和哪个已成交客户画像最像？"
        """
        query_vec = await self._embedder.embed_single(query_text)

        results = []
        for cust_id, cust_vec in self._store.items():
            sim = self._cosine_similarity(query_vec, cust_vec.embedding)
            results.append(SearchResult(
                customer_id=cust_id,
                similarity=sim,
                metadata=cust_vec.metadata,
            ))

        results.sort(key=lambda r: r.similarity, reverse=True)
        return results[:top_k]

    async def search_objection_response(
        self, customer_question: str, top_k: int = 3
    ) -> List[SearchResult]:
        """
        异议语义检索：
        销售输入客户问题 → 返回历史上最成功的回应案例

        这是"AI 销售教练"的 RAG 增强版本：
        不仅有规则库的固定回应，还能检索到真实案例中的最佳实践。
        """
        query_vec = await self._embedder.embed_single(customer_question)

        # 模拟已存储的成功案例（实际部署时从 CRM 读取）
        # 此处展示架构，实际案例在 demo_rag 中演示
        return []

    async def recommend_content(
        self, customer_id: str, top_k: int = 5
    ) -> List[Dict]:
        """
        内容推荐：基于客户兴趣向量推荐最匹配的内容
        对应 Polar Growth OS "交叉推荐"能力
        """
        if customer_id not in self._store:
            return []

        cust_vec = self._store[customer_id]
        # 基于客户 metadata 的兴趣标签推荐
        tags = cust_vec.metadata.get("interest_tags", [])
        # RAG: 检索内容库中与客户兴趣最匹配的内容
        return []

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """余弦相似度"""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# ═══════════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════════

async def demo_rag():
    """演示向量存储 + RAG 检索"""
    store = VectorStore()

    print("=" * 70)
    print("🔮 pgvector RAG — 客户语义检索演示")
    print("=" * 70)

    # 插入示例客户
    customers = [
        ("cust_001", "52岁企业主 去过冰岛非洲 预算30-50万 想去看帝企鹅 关注南极12个月",
         {"name": "王总", "tier": "A", "polar_score": 87, "purchased": False}),
        ("cust_002", "35岁互联网高管 走过70个国家 头等舱飞80段 想要安静的数字排毒之旅",
         {"name": "Linda", "tier": "A", "polar_score": 82, "purchased": False}),
        ("cust_003", "60岁退休医生 去过肯尼亚加拉帕戈斯 摄影爱好者 预算20万以内",
         {"name": "张医生", "tier": "B", "polar_score": 65, "purchased": False}),
        ("cust_004", "45岁女企业家 去年已购南极半岛 现在想升级北极格陵兰豪华线",
         {"name": "陈总", "tier": "S", "polar_score": 95, "purchased": True}),
        ("cust_005", "28岁自媒体博主 穷游为主 想去南极但预算有限 求3万以内方案",
         {"name": "小杨", "tier": "C", "polar_score": 15, "purchased": False}),
    ]

    for cust_id, text, meta in customers:
        await store.insert(cust_id, text, meta)

    print(f"\n已插入 {len(customers)} 位客户向量 (1536维)")

    # 查询 1: 找类似"陈总"的客户（已购南极的高端客户，用于交叉推荐北极）
    print("\n🔍 查询 1: '高净值女性 已购南极 想升级北极 热爱探险'")
    results = await store.search_similar("高净值女性 已购南极 想升级北极 热爱探险", top_k=3)
    for r in results:
        print(f"  {r.customer_id} | 相似度: {r.similarity:.3f} | {r.metadata['name']} ({r.metadata['tier']}级)")

    # 查询 2: 找潜在高端客户
    print("\n🔍 查询 2: '企业主 高预算 深度旅行体验 直升机 探险'")
    results = await store.search_similar("企业主 高预算 深度旅行体验 直升机 探险", top_k=3)
    for r in results:
        print(f"  {r.customer_id} | 相似度: {r.similarity:.3f} | {r.metadata['name']} ({r.metadata['tier']}级)")

    # 查询 3: 剔除低意向（穷游类）
    print("\n🔍 查询 3: '预算有限 穷游 学生 低价'")
    results = await store.search_similar("预算有限 穷游 学生 低价", top_k=3)
    for r in results:
        print(f"  {r.customer_id} | 相似度: {r.similarity:.3f} | {r.metadata['name']} ({r.metadata['tier']}级) — {'⚠️ 低价值' if r.metadata['tier'] == 'C' else '✅'}")

    print("\n💡 实际部署: pip install pgvector && 将 Store 替换为 PostgreSQL + pgvector")


if __name__ == "__main__":
    asyncio.run(demo_rag())
