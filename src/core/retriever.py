"""
Graph-RAG 检索引擎 (Graph-RAG Retriever)

参考 LightRAG 的实体级+关系级双层检索和 GraphRAG 的社区检测机制，
实现多层次的智能检索系统。不依赖外部向量库，使用内置 TF-IDF 做文本相似度匹配。

检索模式:
1. 实体检索 — 精确/模糊匹配实体，返回关联子图
2. 关系检索 — 按谓词类型检索三元组链
3. 语义检索 — 基于 TF-IDF 的文本相似度
4. 混合检索 — 多路召回 + 置信度加权融合

GraphRAG 增强检索:
5. Local Search — 细粒度实体级检索，基于实体邻居扩展
6. Global Search — 社区级摘要检索，基于社区结构的高层次概念检索
7. 智能策略选择 — 根据查询特征自动选择最佳检索模式

排序策略:
- 置信度加权：综合置信度、相关性、新鲜度、访问频率
- RRF 融合：多路检索结果的 Reciprocal Rank Fusion

上下文构建:
- 将检索结果组装为 LLM 可消费的结构化上下文
- 按相关性排序，截断到 token 限制
"""

import logging
import math
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .knowledge_graph import KnowledgeGraph, TypedTriple, SubGraph, Community
from ..utils.config import get_config

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 检索结果
# ─────────────────────────────────────────────

class SearchMode(Enum):
    """检索模式枚举"""
    LOCAL = "local"       # Local Search: 实体邻居检索
    GLOBAL = "global"     # Global Search: 社区级检索
    HYBRID = "hybrid"     # 混合检索: Local + Global
    AUTO = "auto"         # 自动选择模式

@dataclass
class RetrievalResult:
    """单条检索结果"""
    triple: TypedTriple
    score: float          # 相关性分数 (0-1)
    source: str           # 检索来源: "entity", "relation", "semantic", "pattern", "local", "global"
    context: str = ""     # 可读的上下文描述
    # 新增：综合排序分数
    weighted_score: float = 0.0  # 加权综合分数
    # 新增：各维度分数
    relevance_score: float = 0.0   # 相关性分数
    confidence_score: float = 0.0  # 置信度分数
    freshness_score: float = 0.0   # 新鲜度分数
    access_score: float = 0.0      # 访问频率分数
    # 新增：社区信息（用于 Global Search）
    community_id: int = -1  # 所属社区 ID，-1 表示未分配

    def __repr__(self):
        return (
            f"RetrievalResult(({self.triple.subject}, {self.triple.predicate}, "
            f"{self.triple.object}), score={self.score:.3f}, source={self.source})"
        )


@dataclass
class RetrievalResponse:
    """完整检索响应"""
    results: List[RetrievalResult]
    query: str
    total_candidates: int = 0
    retrieval_modes: List[str] = field(default_factory=list)
    # 新增：检索模式信息
    search_mode: SearchMode = SearchMode.AUTO
    # 新增：社区统计信息
    communities_searched: int = 0  # 搜索的社区数量
    entities_found: int = 0  # 找到的实体数量

    @property
    def top_entities(self) -> Set[str]:
        """检索命中的顶级实体"""
        entities = set()
        for r in self.results:
            entities.add(r.triple.subject)
            entities.add(r.triple.object)
        return entities

    @property
    def top_triples(self) -> List[TypedTriple]:
        """按相关性排序的三元组"""
        return [r.triple for r in self.results]


# ─────────────────────────────────────────────
# 轻量 TF-IDF 引擎
# ─────────────────────────────────────────────

class _TFIDFIndex:
    """
    内置轻量 TF-IDF 索引，不依赖外部库。
    
    性能优化：
    - 使用增量更新策略，避免全量重建 IDF
    - 文档增删时标记 dirty，搜索时按需重建
    - 支持文档更新时的增量 TF 计算
    """

    def __init__(self):
        self._docs: Dict[str, str] = {}       # doc_id → text
        self._idf: Dict[str, float] = {}      # term → idf
        self._tf: Dict[str, Dict[str, float]] = {}  # doc_id → {term: tf}
        self._doc_freq: Dict[str, int] = defaultdict(int)  # term → 文档频率（增量维护）
        self._dirty = True
        self._doc_count = 0  # 文档总数缓存

    def add_document(self, doc_id: str, text: str):
        """
        添加文档 — 支持增量更新。
        
        如果文档已存在，先移除旧文档再添加新文档，
        确保 IDF 统计准确。
        """
        # 如果文档已存在，先移除旧版本（确保 IDF 准确）
        if doc_id in self._docs:
            self.remove_document(doc_id)
        
        self._docs[doc_id] = text
        self._doc_count += 1
        
        # 计算 TF
        tokens = self._tokenize(text)
        if not tokens:
            self._tf[doc_id] = {}
            self._dirty = True
            return
        
        counts = defaultdict(int)
        for t in tokens:
            counts[t] += 1
        total = len(tokens)
        self._tf[doc_id] = {t: c / total for t, c in counts.items()}
        
        # 增量更新文档频率（用于后续 IDF 计算）
        for term in counts.keys():
            self._doc_freq[term] += 1
        
        self._dirty = True

    def remove_document(self, doc_id: str):
        """
        移除文档 — 支持增量更新。
        
        更新文档频率统计，标记需要重建 IDF。
        """
        if doc_id not in self._docs:
            return
        
        # 减少文档频率计数
        tf_map = self._tf.get(doc_id, {})
        for term in tf_map.keys():
            self._doc_freq[term] -= 1
            if self._doc_freq[term] <= 0:
                del self._doc_freq[term]
        
        self._docs.pop(doc_id, None)
        self._tf.pop(doc_id, None)
        self._doc_count -= 1
        self._dirty = True

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        搜索，返回 [(doc_id, score)]。
        
        如果索引标记为 dirty，先重建 IDF。
        使用缓存的 IDF 值加速查询。
        """
        if self._dirty:
            self._rebuild_idf()

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = {}
        for doc_id, tf_map in self._tf.items():
            score = 0.0
            for qt in query_tokens:
                if qt in tf_map:
                    idf = self._idf.get(qt, 0.0)
                    score += tf_map[qt] * idf
            if score > 0:
                scores[doc_id] = score

        # 排序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def _rebuild_idf(self):
        """
        重建 IDF — 使用增量维护的文档频率。
        
        性能优化：
        - 使用缓存的 _doc_freq 避免全量扫描所有文档
        - 时间复杂度从 O(N*avg_doc_length) 降到 O(unique_terms)
        """
        n = self._doc_count
        if n == 0:
            self._idf = {}
            self._dirty = False
            return

        # 使用增量维护的文档频率计算 IDF
        # 避免每次扫描所有文档的 TF 映射
        self._idf = {
            term: math.log((n + 1) / (df + 1)) + 1
            for term, df in self._doc_freq.items()
        }
        self._dirty = False

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """简单分词: 中文按字，英文按词"""
        tokens = []
        # 英文词
        for word in re.findall(r'[a-zA-Z_]\w*', text.lower()):
            tokens.append(word)
        # 中文字/词 (bigram)
        chinese = re.findall(r'[\u4e00-\u9fff]+', text)
        for seg in chinese:
            # unigram
            for ch in seg:
                tokens.append(ch)
            # bigram
            for i in range(len(seg) - 1):
                tokens.append(seg[i:i+2])
        return tokens


# ─────────────────────────────────────────────
# Graph-RAG 检索器
# ─────────────────────────────────────────────

class GraphRetriever:
    """
    Graph-RAG 检索器

    实现多层次检索模式 + 融合排序:
    1. 实体检索: 精确/模糊匹配实体名，返回关联子图
    2. 关系检索: 按谓词类型检索三元组链
    3. 语义检索: TF-IDF 文本相似度
    4. 混合检索: 多路召回 + RRF 融合排序
    
    GraphRAG 增强:
    5. Local Search: 基于实体邻居的细粒度检索
    6. Global Search: 基于社区结构的高层次检索
    7. 智能策略选择: 根据查询特征自动选择最佳模式
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        self._kg = knowledge_graph
        self._tfidf = _TFIDFIndex()
        self._indexed = False
        # 从配置读取参数
        self._config = get_config().graphrag

    def build_index(self):
        """构建/重建文本索引"""
        self._tfidf = _TFIDFIndex()
        for triple in self._kg:
            text = f"{triple.subject} {triple.predicate} {triple.object}"
            self._tfidf.add_document(triple.id, text)
        self._indexed = True
        logger.debug(f"GraphRetriever: 索引已构建, {self._kg.size} 条三元组")

    def _ensure_index(self):
        """确保索引已构建"""
        if not self._indexed or self._tfidf._dirty:
            self.build_index()
    
    # ─────────────────────────────────────────
    # Local Search: 细粒度实体检索
    # ─────────────────────────────────────────

    def local_search(
        self,
        query: str,
        top_k: int = None,
        depth: int = None,
    ) -> RetrievalResponse:
        """
        Local Search: 细粒度实体级检索
        
        基于实体及其直接邻居进行精确检索，适合具体事实查询。
        检索策略：
        1. 从查询中提取实体
        2. 对每个实体进行 BFS 邻居扩展
        3. 收集相关三元组并按相关性排序
        
        边界处理：
        - 空实体列表：回退到语义检索
        - 空子图结果：返回空结果而非崩溃
        - 单节点图：正常处理，返回该节点的三元组

        Args:
            query: 查询文本
            top_k: 最大返回数，默认从配置读取
            depth: 邻居扩展深度，默认从配置读取

        Returns:
            RetrievalResponse 包含检索结果
        """
        # 从配置获取默认参数
        top_k = top_k or self._config.local_search_top_k
        depth = depth or self._config.local_search_depth
        
        # 从查询中提取候选实体
        candidate_entities = self._extract_entities_from_query(query)
        
        if not candidate_entities:
            # 未识别到实体，回退到语义检索
            logger.debug("Local Search: 未识别到实体，回退到语义检索")
            return self._fallback_semantic_search(query, top_k, SearchMode.LOCAL)
        
        all_results = []
        
        for entity in candidate_entities:
            # 获取实体邻居子图
            subgraph = self._kg.neighbors(entity, depth=depth)
            
            # 边界检查：处理空子图情况（实体存在但无关联三元组）
            if not subgraph or not subgraph.triples:
                logger.debug(f"Local Search: 实体 '{entity}' 无邻居子图")
                continue
            
            for t in subgraph.triples:
                # 计算相关性分数
                relevance = self._calculate_entity_relevance(t, entity, query)
                # 创建检索结果
                result = RetrievalResult(
                    triple=t,
                    score=relevance,
                    source="local",
                    context=f"Local Search: 实体 '{entity}' 的邻居三元组",
                )
                # 计算加权分数
                result = self._calculate_weighted_score(result, query)
                all_results.append(result)
        
        # 边界检查：处理所有实体都无结果的情况
        if not all_results:
            logger.debug("Local Search: 所有实体均无邻居子图，回退到语义检索")
            return self._fallback_semantic_search(query, top_k, SearchMode.LOCAL)
        
        # 去重并排序
        all_results = self._deduplicate(all_results)
        all_results.sort(key=lambda r: r.weighted_score, reverse=True)
        
        return RetrievalResponse(
            results=all_results[:top_k],
            query=query,
            total_candidates=len(all_results),
            retrieval_modes=["local"],
            search_mode=SearchMode.LOCAL,
            entities_found=len(set(r.triple.subject for r in all_results) | 
                              set(r.triple.object for r in all_results)),
        )

    def _calculate_entity_relevance(
        self,
        triple: TypedTriple,
        entity: str,
        query: str,
    ) -> float:
        """
        计算三元组与实体的相关性分数
        
        相关性计算因素：
        1. 实体匹配度：三元组是否直接包含目标实体
        2. 置信度：三元组的置信度
        3. 距离衰减：与目标实体的距离
        """
        base_score = triple.confidence
        
        # 检查实体是否直接参与三元组
        if entity == triple.subject or entity == triple.object:
            # 实体直接参与，高分
            entity_match = 1.0
        else:
            # 实体间接相关，适度降分
            entity_match = 0.7
        
        # 检查谓词是否出现在查询中
        predicate_match = 1.0
        if triple.predicate.lower() in query.lower():
            predicate_match = 1.2
        
        return min(1.0, base_score * entity_match * predicate_match)

    # ─────────────────────────────────────────
    # Global Search: 社区级摘要检索
    # ─────────────────────────────────────────

    def global_search(
        self,
        query: str,
        top_k: int = None,
        num_communities: int = None,
    ) -> RetrievalResponse:
        """
        Global Search: 社区级摘要检索
        
        基于社区结构进行高层次概念检索，适合开放性问题。
        检索策略：
        1. 执行社区检测（带超时保护）
        2. 根据查询语义选择相关社区
        3. 从每个社区提取代表性三元组
        
        边界处理：
        - 空图/单节点图：社区检测返回空列表，回退到语义检索
        - 社区检测超时：捕获异常并回退到语义检索
        - 无相关社区：返回空结果

        Args:
            query: 查询文本
            top_k: 最大返回数
            num_communities: 搜索的社区数量

        Returns:
            RetrievalResponse 包含检索结果
        """
        # 从配置获取默认参数
        top_k = top_k or self._config.local_search_top_k
        num_communities = num_communities or self._config.global_search_communities
        
        # 从配置读取社区检测超时时间（默认 30 秒）
        timeout_seconds = getattr(self._config, 'community_detection_timeout', 30)
        
        try:
            # 使用信号或超时机制保护社区检测（大图可能耗时很长）
            communities = self._detect_communities_with_timeout(timeout_seconds)
        except TimeoutError:
            logger.warning(f"Global Search: 社区检测超时（>{timeout_seconds}s），回退到语义检索")
            return self._fallback_semantic_search(query, top_k, SearchMode.GLOBAL)
        except Exception as e:
            logger.warning(f"Global Search: 社区检测失败: {e}，回退到语义检索")
            return self._fallback_semantic_search(query, top_k, SearchMode.GLOBAL)
        
        # 边界检查：处理空图、单节点图、无边图的情况
        if not communities:
            logger.debug("Global Search: 无社区结构（可能图为空或过于稀疏），回退到语义检索")
            return self._fallback_semantic_search(query, top_k, SearchMode.GLOBAL)
        
        # 选择相关社区
        relevant_communities = self._select_relevant_communities(
            query, communities, num_communities
        )
        
        # 边界检查：处理无相关社区的情况
        if not relevant_communities:
            logger.debug("Global Search: 未找到相关社区，回退到语义检索")
            return self._fallback_semantic_search(query, top_k, SearchMode.GLOBAL)
        
        all_results = []
        
        for community in relevant_communities:
            # 从社区提取代表性三元组
            community_results = self._extract_community_representatives(
                community, query, top_k
            )
            all_results.extend(community_results)
        
        # 边界检查：处理社区中无三元组的情况
        if not all_results:
            logger.debug("Global Search: 相关社区中无三元组，回退到语义检索")
            return self._fallback_semantic_search(query, top_k, SearchMode.GLOBAL)
        
        # 去重并排序
        all_results = self._deduplicate(all_results)
        all_results.sort(key=lambda r: r.weighted_score, reverse=True)
        
        return RetrievalResponse(
            results=all_results[:top_k],
            query=query,
            total_candidates=len(all_results),
            retrieval_modes=["global"],
            search_mode=SearchMode.GLOBAL,
            communities_searched=len(relevant_communities),
            entities_found=len(set(r.triple.subject for r in all_results) | 
                              set(r.triple.object for r in all_results)),
        )

    def _detect_communities_with_timeout(self, timeout_seconds: int) -> List[Any]:
        """
        带超时保护的社区检测。
        
        对大图的社区检测可能耗时很长，使用超时机制防止阻塞。
        当前实现使用简单的计时检查，未来可升级为信号或线程机制。
        
        Args:
            timeout_seconds: 超时时间（秒）
            
        Returns:
            社区列表，如果超时则抛出 TimeoutError
            
        Raises:
            TimeoutError: 当社区检测超过指定时间
        """
        import signal
        
        # 检查平台是否支持信号机制（Windows 不支持 SIGALRM）
        if hasattr(signal, 'SIGALRM'):
            # Unix/Linux/Mac 平台：使用信号机制
            def timeout_handler(signum, frame):
                raise TimeoutError(f"社区检测超时（>{timeout_seconds}秒）")
            
            # 设置超时信号
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            try:
                communities = self._kg.detect_communities()
                return communities
            finally:
                # 恢复原始信号处理器并取消闹钟
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        else:
            # Windows 平台：使用简单计时检查（非精确超时）
            start_time = time.time()
            
            # 先检查图规模，如果过大则直接跳过社区检测
            graph_size = self._kg.size
            # 从配置读取大图阈值
            large_graph_threshold = getattr(self._config, 'large_graph_threshold', 10000)
            
            if graph_size > large_graph_threshold:
                logger.warning(f"图规模过大（{graph_size} 三元组），跳过社区检测以避免长时间阻塞")
                return []
            
            # 对于中等规模图，执行检测但记录时间
            communities = self._kg.detect_communities()
            elapsed = time.time() - start_time
            
            if elapsed > timeout_seconds:
                logger.warning(f"社区检测耗时 {elapsed:.1f}s，超过阈值 {timeout_seconds}s")
            
            return communities

    def _select_relevant_communities(
        self,
        query: str,
        communities: List[Community],
        num_communities: int,
    ) -> List[Community]:
        """
        根据查询语义选择相关社区
        
        选择策略：
        1. 计算查询与每个社区核心实体的语义相关性
        2. 按相关性排序选择 Top-N 社区
        """
        query_lower = query.lower()
        community_scores = []
        
        for community in communities:
            # 计算查询与社区核心实体的匹配度
            score = 0.0
            
            # 检查核心实体是否出现在查询中
            for hub_entity in community.hub_entities:
                if hub_entity.lower() in query_lower:
                    score += 0.5
                elif query_lower in hub_entity.lower():
                    score += 0.3
            
            # 检查社区内实体名称是否出现在查询中
            for entity in list(community.entities)[:20]:  # 限制检查数量
                if entity.lower() in query_lower:
                    score += 0.1
            
            # 社区规模归一化加分（大社区适度加分）
            score += min(0.2, community.size / 100)
            
            community_scores.append((community, score))
        
        
        # 按分数排序
        community_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 如果没有匹配的社区，选择最大的几个社区
        if community_scores[0][1] == 0:
            return sorted(communities, key=lambda c: c.size, reverse=True)[:num_communities]
        
        return [c for c, _ in community_scores[:num_communities]]

    def _extract_community_representatives(
        self,
        community: Community,
        query: str,
        per_community_limit: int,
    ) -> List[RetrievalResult]:
        """
        从社区中提取代表性三元组
        
        提取策略：
        1. 优先选择高置信度三元组
        2. 优先选择包含核心实体的三元组
        3. 优先选择与查询相关的三元组
        """
        per_community_limit = per_community_limit or self._config.global_search_per_community
        
        # 获取社区内三元组
        community_triples = self._kg.get_community_triples(community.community_id)
        
        results = []
        query_lower = query.lower()
        
        for t in community_triples:
            # 计算基础相关性
            relevance = t.confidence
            
            # 检查是否包含核心实体
            if t.subject in community.hub_entities or t.object in community.hub_entities:
                relevance *= 1.2
            
            # 检查与查询的语义相关性
            if any(word in query_lower for word in [t.subject.lower(), t.predicate.lower(), t.object.lower()]):
                relevance *= 1.3
            
            result = RetrievalResult(
                triple=t,
                score=min(1.0, relevance),
                source="global",
                context=f"Global Search: 社区 {community.community_id} (核心实体: {', '.join(community.hub_entities[:3])})",
                community_id=community.community_id,
            )
            # 计算加权分数
            result = self._calculate_weighted_score(result, query)
            results.append(result)
        
        
        # 排序并限制数量
        results.sort(key=lambda r: r.weighted_score, reverse=True)
        return results[:per_community_limit]

    # ─────────────────────────────────────────
    # 智能策略选择
    # ─────────────────────────────────────────

    def smart_search(
        self,
        query: str,
        top_k: int = None,
        mode: str = None,
    ) -> RetrievalResponse:
        """
        智能检索：根据查询特征自动选择最佳检索模式

        策略选择规则：
        1. 查询包含明确的实体名 → Local Search
        2. 查询是开放性问题 → Global Search
        3. 查询包含多个关键词 → 混合检索

        Args:
            query: 查询文本
            top_k: 最大返回数
            mode: 强制模式 ("local", "global", "hybrid", "auto")

        Returns:
            RetrievalResponse 包含检索结果
        """
        top_k = top_k or get_config().retriever.default_top_k
        mode = mode or self._config.hybrid_strategy
        
        # 解析模式
        if mode == "local":
            return self.local_search(query, top_k)
        elif mode == "global":
            return self.global_search(query, top_k)
        elif mode == "hybrid":
            return self._hybrid_search(query, top_k)
        else:
            # Auto 模式：自动选择
            return self._auto_select_search(query, top_k)

    def _auto_select_search(self, query: str, top_k: int) -> RetrievalResponse:
        """
        自动选择最佳检索模式

        选择依据：
        1. 实体识别数量
        2. 查询关键词数量
        3. 查询类型判断
        """
        # 分析查询特征
        entities_in_query = self._extract_entities_from_query(query)
        keywords_in_query = self._extract_keywords(query)
        
        # 判断查询类型
        is_question = any(q in query for q in ["什么", "如何", "怎么", "为什么", "哪些", "?", "？"])
        entity_count = len(entities_in_query)
        keyword_count = len(keywords_in_query)
        
        # 选择策略
        # 如果识别到实体，且实体数量较少，使用 Local Search
        if entity_count > 0 and entity_count <= self._config.auto_local_threshold:
            logger.debug(f"Auto 选择 Local Search: 识别到 {entity_count} 个实体")
            return self.local_search(query, top_k)
        
        # 如果是开放性问题，使用 Global Search
        if is_question and keyword_count >= self._config.auto_global_threshold:
            logger.debug(f"Auto 选择 Global Search: 开放性问题，{keyword_count} 个关键词")
            return self.global_search(query, top_k)
        
        # 其他情况使用混合检索
        logger.debug(f"Auto 选择 Hybrid Search: {entity_count} 实体, {keyword_count} 关键词")
        return self._hybrid_search(query, top_k)

    def _hybrid_search(self, query: str, top_k: int) -> RetrievalResponse:
        """
        混合检索：Local + Global 结合

        策略：
        1. 执行 Local Search 和 Global Search
        2. 按权重融合结果
        """
        local_weight = self._config.hybrid_local_weight
        global_weight = self._config.hybrid_global_weight
        
        # 执行两种检索
        local_results = self.local_search(query, top_k)
        global_results = self.global_search(query, top_k)
        
        # 合并结果
        all_results = []
        
        # Local 结果加权
        for r in local_results.results:
            r.weighted_score *= local_weight
            all_results.append(r)
        
        # Global 结果加权
        for r in global_results.results:
            r.weighted_score *= global_weight
            all_results.append(r)
        
        # 去重并排序
        all_results = self._deduplicate(all_results)
        all_results.sort(key=lambda r: r.weighted_score, reverse=True)
        
        return RetrievalResponse(
            results=all_results[:top_k],
            query=query,
            total_candidates=len(all_results),
            retrieval_modes=["local", "global"],
            search_mode=SearchMode.HYBRID,
            communities_searched=global_results.communities_searched,
            entities_found=len(set(r.triple.subject for r in all_results) | 
                              set(r.triple.object for r in all_results)),
        )

    def _fallback_semantic_search(
        self,
        query: str,
        top_k: int,
        mode: SearchMode,
    ) -> RetrievalResponse:
        """
        回退到语义检索（当 Local/Global 无法执行时）
        """
        semantic_results = self.retrieve_by_semantic(query, top_k)
        
        # 为结果添加加权分数
        for r in semantic_results:
            r = self._calculate_weighted_score(r, query)
        
        return RetrievalResponse(
            results=semantic_results,
            query=query,
            total_candidates=len(semantic_results),
            retrieval_modes=["semantic"],
            search_mode=mode,
        )

    # ─────────────────────────────────────────
    # 置信度加权排序
    # ─────────────────────────────────────────

    def _calculate_weighted_score(
        self,
        result: RetrievalResult,
        query: str,
    ) -> RetrievalResult:
        """
        计算加权综合分数

        综合以下维度：
        1. 相关性分数 (relevance)
        2. 置信度分数 (confidence)
        3. 新鲜度分数 (freshness)
        4. 访问频率分数 (access)

        Args:
            result: 检索结果
            query: 查询文本

        Returns:
            更新了加权分数的检索结果
        """
        config = self._config
        
        # 1. 相关性分数：使用已有的 score
        result.relevance_score = result.score
        
        # 2. 置信度分数：直接使用三元组置信度
        result.confidence_score = result.triple.confidence
        
        # 3. 新鲜度分数：基于时间戳计算衰减
        result.freshness_score = self._calculate_freshness(result.triple.timestamp)
        
        # 4. 访问频率分数：基于访问次数归一化
        result.access_score = self._normalize_access_count(result.triple.access_count)
        
        # 计算加权综合分数
        result.weighted_score = (
            result.relevance_score * config.weight_relevance +
            result.confidence_score * config.weight_confidence +
            result.freshness_score * config.weight_freshness +
            result.access_score * config.weight_access
        )
        
        return result

    def _calculate_freshness(self, timestamp: float) -> float:
        """
        计算新鲜度分数

        基于时间戳计算指数衰减分数，越新的知识分数越高。
        衰减公式：e^(-age / decay_period)
        """
        if timestamp == 0:
            return 0.5  # 无时间戳信息，返回中等分数
        
        current_time = time.time()
        age = current_time - timestamp
        decay_period = self._config.freshness_decay_seconds
        
        # 指数衰减
        freshness = math.exp(-age / decay_period)
        return freshness

    def _normalize_access_count(self, access_count: int) -> float:
        """
        归一化访问次数

        使用 sigmoid 函数将访问次数映射到 (0, 1) 区间。
        """
        # 使用 sigmoid 归一化：1 / (1 + e^(-x/10))
        # x/10 用于调整曲线斜率
        normalized = 1.0 / (1.0 + math.exp(-access_count / 10.0))
        return normalized

    def _extract_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词

        提取策略：
        1. 中文词汇（2字以上）
        2. 英文单词
        3. 过滤停用词
        """
        # 简单停用词列表
        stopwords = {"的", "是", "在", "有", "和", "了", "与", "这", "那", "为", "以", "及",
                    "the", "a", "an", "is", "are", "was", "were", "be", "been",
                    "have", "has", "had", "do", "does", "did", "will", "would",
                    "could", "should", "may", "might", "must", "shall"}
        
        keywords = []
        
        # 提取中文词汇（简单 2-gram）
        chinese_segs = re.findall(r'[\u4e00-\u9fff]{2,}', query)
        keywords.extend(chinese_segs)
        
        # 提取英文单词
        english_words = re.findall(r'[a-zA-Z_]\w{2,}', query.lower())
        keywords.extend(english_words)
        
        # 过滤停用词
        keywords = [kw for kw in keywords if kw not in stopwords]
        
        return keywords

    # ─── 实体检索 ───

    def retrieve_by_entity(
        self,
        entity: str,
        depth: int = None,
        fuzzy: bool = True,
        top_k: int = None,
    ) -> List[RetrievalResult]:
        """
        实体级检索: 查找实体及其关联子图

        Args:
            entity: 实体名称
            depth: 图遍历深度，默认从配置读取
            fuzzy: 是否启用模糊匹配
            top_k: 最大返回数，默认从配置读取
        """
        # 从配置获取默认值
        depth = depth if depth is not None else get_config().retriever.entity_depth
        top_k = top_k if top_k is not None else get_config().retriever.default_top_k
        fuzzy_threshold = get_config().retriever.fuzzy_match_threshold
        
        results = []

        # 1. 精确匹配
        matched_entities = set()
        if entity in self._kg.entities():
            matched_entities.add(entity)

        # 2. 模糊匹配 (实体名包含查询词或反之)
        if fuzzy:
            entity_lower = entity.lower()
            for ent in self._kg.entities():
                # 使用配置的模糊匹配阈值
                if entity_lower in ent.lower() or ent.lower() in entity_lower:
                    matched_entities.add(ent)

        # 3. 对每个匹配实体获取子图
        for ent in matched_entities:
            subgraph = self._kg.neighbors(ent, depth=depth)
            for t in subgraph.triples:
                # 计算分数: 精确匹配最高, 模糊匹配次之, 距离衰减
                score = t.confidence
                if ent == entity:
                    score *= fuzzy_threshold  # 使用配置的精确匹配权重
                else:
                    score *= fuzzy_threshold * 0.8  # 模糊匹配降权

                results.append(RetrievalResult(
                    triple=t,
                    score=score,
                    source="entity",
                    context=f"通过实体 '{ent}' 关联",
                ))

        # 去重 + 排序
        results = self._deduplicate(results)
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    # ─── 关系检索 ───

    def retrieve_by_relation(
        self,
        predicate: Optional[str] = None,
        subject: Optional[str] = None,
        obj: Optional[str] = None,
        top_k: int = None,
    ) -> List[RetrievalResult]:
        """
        关系级检索: 按谓词/主语/宾语检索三元组

        Args:
            predicate: 谓词过滤
            subject: 主语过滤
            obj: 宾语过滤
            top_k: 最大返回数，默认从配置读取
        """
        top_k = top_k if top_k is not None else get_config().retriever.default_top_k
        
        triples = self._kg.query(
            subject=subject,
            predicate=predicate,
            obj=obj,
        )
        results = [
            RetrievalResult(
                triple=t,
                score=t.confidence,
                source="relation",
                context=f"关系匹配: {predicate or '*'}",
            )
            for t in triples
        ]
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    # ─── 语义检索 ───

    def retrieve_by_semantic(
        self,
        query: str,
        top_k: int = None,
    ) -> List[RetrievalResult]:
        """
        语义检索: 使用 TF-IDF 文本相似度

        Args:
            query: 查询文本
            top_k: 最大返回数，默认从配置读取
        """
        top_k = top_k if top_k is not None else get_config().retriever.default_top_k
        
        self._ensure_index()
        tfidf_results = self._tfidf.search(query, top_k=top_k)

        results = []
        # 归一化分数
        max_score = tfidf_results[0][1] if tfidf_results else 1.0
        for tid, score in tfidf_results:
            triple = self._kg.get_triple(tid)
            if triple:
                normalized_score = (score / max_score) * triple.confidence
                results.append(RetrievalResult(
                    triple=triple,
                    score=normalized_score,
                    source="semantic",
                    context=f"语义匹配 (TF-IDF score={score:.3f})",
                ))

        return results

    # ─── 混合检索 (核心) ───

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        modes: Optional[List[str]] = None,
        entity_depth: int = None,
        search_mode: Optional[str] = None,
    ) -> RetrievalResponse:
        """
        混合检索: 多路召回 + RRF 融合排序

        此方法保持向后兼容，同时支持新的检索模式。
        
        Args:
            query: 查询文本
            top_k: 最终返回数
            modes: 检索模式列表, 默认 ["entity", "semantic"]
            entity_depth: 实体检索深度
            search_mode: 检索模式 ("local", "global", "hybrid", "auto")
                        如果指定，将使用智能检索模式覆盖 modes 参数

        Returns:
            RetrievalResponse 融合结果
        """
        # 从配置获取默认值
        top_k = top_k or get_config().retriever.default_top_k
        entity_depth = entity_depth or get_config().retriever.entity_depth
        
        # 如果指定了新的检索模式，使用智能检索
        # 否则使用原来的 modes 参数
        if search_mode is not None and search_mode in ("local", "global", "hybrid", "auto"):
            return self.smart_search(query, top_k, mode=search_mode)

        if modes is None:
            modes = ["entity", "semantic"]

        all_results: List[RetrievalResult] = []
        total_candidates = 0

        # 1. 实体检索
        if "entity" in modes:
            # 从查询中提取候选实体
            candidate_entities = self._extract_entities_from_query(query)
            for ent in candidate_entities:
                entity_results = self.retrieve_by_entity(
                    ent, depth=entity_depth, top_k=top_k
                )
                # 为结果计算加权分数
                for r in entity_results:
                    r = self._calculate_weighted_score(r, query)
                all_results.extend(entity_results)
                total_candidates += len(entity_results)

        # 2. 关系检索
        if "relation" in modes:
            # 从查询中提取谓词
            predicates = self._extract_predicates_from_query(query)
            for pred in predicates:
                relation_results = self.retrieve_by_relation(
                    predicate=pred, top_k=top_k
                )
                for r in relation_results:
                    r = self._calculate_weighted_score(r, query)
                all_results.extend(relation_results)
                total_candidates += len(relation_results)

        # 3. 语义检索
        if "semantic" in modes:
            semantic_results = self.retrieve_by_semantic(query, top_k=top_k)
            for r in semantic_results:
                r = self._calculate_weighted_score(r, query)
            all_results.extend(semantic_results)
            total_candidates += len(semantic_results)

        # RRF 融合排序
        fused = self._rrf_fusion(all_results, top_k=top_k)

        return RetrievalResponse(
            results=fused,
            query=query,
            total_candidates=total_candidates,
            retrieval_modes=modes,
            search_mode=SearchMode.HYBRID,
            entities_found=len(set(r.triple.subject for r in fused) | 
                              set(r.triple.object for r in fused)),
        )

    # ─── 内部工具方法 ───

    def _extract_entities_from_query(self, query: str) -> List[str]:
        """从查询文本中提取候选实体名"""
        candidates = []
        known_entities = self._kg.entities()

        # 精确匹配: 查询中包含的已知实体
        for ent in known_entities:
            if ent in query:
                candidates.append(ent)

        # 如果没有精确匹配，用查询本身做模糊匹配
        if not candidates:
            # 中文分词: 提取连续中文片段
            chinese_segs = re.findall(r'[\u4e00-\u9fff]{2,}', query)
            candidates.extend(chinese_segs)
            # 英文词
            english_words = re.findall(r'[a-zA-Z_]\w{2,}', query)
            candidates.extend(english_words)

        return candidates[:5]  # 最多5个候选

    def _extract_predicates_from_query(self, query: str) -> List[str]:
        """从查询中提取谓词关键词"""
        predicates = []
        known_predicates = self._kg.predicates()

        for pred in known_predicates:
            if pred in query or pred.replace("_", " ") in query:
                predicates.append(pred)

        return predicates[:3]

    @staticmethod
    def _deduplicate(results: List[RetrievalResult]) -> List[RetrievalResult]:
        """去重: 同一三元组保留最高分"""
        best = {}
        for r in results:
            tid = r.triple.id
            if tid not in best or r.score > best[tid].score:
                best[tid] = r
        return list(best.values())

    @staticmethod
    def _rrf_fusion(
        results: List[RetrievalResult],
        top_k: int = 20,
        k: int = None,
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion (RRF) 排序融合

        k 从 ConfigManager 读取，默认 60 (同 Elasticsearch)。
        """
        # 从 ConfigManager 读取 RRF 平滑常数
        if k is None:
            k = get_config().retriever.rrf_k
        # 按 source 分组排序
        by_source: Dict[str, List[RetrievalResult]] = defaultdict(list)
        for r in results:
            by_source[r.source].append(r)

        for source_results in by_source.values():
            source_results.sort(key=lambda r: r.score, reverse=True)

        # 计算 RRF 分数
        rrf_scores: Dict[str, float] = defaultdict(float)
        result_map: Dict[str, RetrievalResult] = {}

        for source_results in by_source.values():
            for rank, r in enumerate(source_results):
                tid = r.triple.id
                rrf_scores[tid] += 1.0 / (k + rank + 1)
                # 保留最高分的 result 对象
                if tid not in result_map or r.score > result_map[tid].score:
                    result_map[tid] = r

        # 按 RRF 分数排序
        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        final = []
        for tid, rrf_score in ranked[:top_k]:
            r = result_map[tid]
            # 用 RRF 分数覆盖原始分数
            final.append(RetrievalResult(
                triple=r.triple,
                score=rrf_score,
                source=r.source,
                context=r.context,
            ))

        return final


# ─────────────────────────────────────────────
# 上下文构建器
# ─────────────────────────────────────────────

class ContextBuilder:
    """
    将检索结果组装为 LLM 可消费的结构化上下文

    输出格式:
    ```
    [知识图谱上下文]
    == 实体定义 ==
    - 燃气调压箱: is_a 设备 (置信度: 0.95)

    == 相关关系 ==
    - 燃气调压箱 has_component 调压器 (置信度: 0.90)

    == 适用规则 ==
    - 如果 设备 is_a 燃气调压箱 那么 requires 维护
    ```
    """

    def __init__(self, max_tokens: int = None):
        """
        Args:
            max_tokens: 上下文最大 token 数, 从 ConfigManager 读取
        """
        self.max_tokens = max_tokens if max_tokens is not None else get_config().retriever.context_max_tokens

    def build(
        self,
        retrieval: RetrievalResponse,
        include_metadata: bool = False,
    ) -> str:
        """
        构建结构化上下文

        Args:
            retrieval: 检索结果
            include_metadata: 是否包含元数据 (来源、时间等)

        Returns:
            格式化的上下文字符串
        """
        if not retrieval.results:
            return "[知识图谱上下文]\n当前无相关知识。"

        # 按类型分组
        definitions = []   # is_a, type_of 等定义性关系
        relations = []     # 其他关系
        rules = []         # 规则 (conditions/actions)

        definition_predicates = {"is_a", "type_of", "subclass_of", "instance_of", "属于", "是"}

        for r in retrieval.results:
            t = r.triple
            if t.predicate in definition_predicates:
                definitions.append((t, r.score))
            elif t.predicate.startswith("_"):
                # 内部谓词 (规则关联)
                rules.append((t, r.score))
            else:
                relations.append((t, r.score))

        lines = ["[知识图谱上下文]"]
        current_tokens = 10  # 预留 header

        # 1. 实体定义
        if definitions:
            lines.append("\n== 实体定义 ==")
            for t, score in definitions:
                line = f"- {t.subject} {t.predicate} {t.object} (置信度: {t.confidence:.2f})"
                est_tokens = len(line) // 2 + 1
                if current_tokens + est_tokens > self.max_tokens:
                    break
                lines.append(line)
                current_tokens += est_tokens

        # 2. 相关关系
        if relations:
            lines.append("\n== 相关关系 ==")
            for t, score in relations:
                line = f"- {t.subject} → {t.predicate} → {t.object} (置信度: {t.confidence:.2f})"
                if include_metadata:
                    line += f" [来源: {t.source}]"
                est_tokens = len(line) // 2 + 1
                if current_tokens + est_tokens > self.max_tokens:
                    break
                lines.append(line)
                current_tokens += est_tokens

        # 3. 规则
        if rules:
            lines.append("\n== 相关规则 ==")
            for t, score in rules:
                line = f"- {t.subject} {t.predicate} {t.object}"
                est_tokens = len(line) // 2 + 1
                if current_tokens + est_tokens > self.max_tokens:
                    break
                lines.append(line)
                current_tokens += est_tokens

        return "\n".join(lines)

    def build_compact(self, retrieval: RetrievalResponse) -> str:
        """紧凑格式: 直接列出三元组，节省 token"""
        if not retrieval.results:
            return ""

        lines = []
        for r in retrieval.results[:15]:  # 最多15条
            t = r.triple
            lines.append(f"({t.subject}, {t.predicate}, {t.object})")

        return "相关知识: " + "; ".join(lines)
