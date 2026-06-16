import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from josie_agents.core.database_config import get_database_config
from josie_agents.memory.base import BaseMemory, MemoryConfig, MemoryItem
from josie_agents.memory.embedding import get_text_embedder, get_dimension
from josie_agents.memory.storage.document_store import SQLiteDocumentStore
from josie_agents.memory.storage.qdrant_store import QdrantConnectionManager
import josie_agents.utils.log as log

class Episode:
    """情景记忆中的单个情景"""

    def __init__(
        self,
        episode_id: str,
        user_id: str,
        session_id: str,
        timestamp: datetime,
        content: str,
        context: Dict[str, Any],
        outcome: Optional[str] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.episode_id = episode_id
        self.user_id = user_id
        self.session_id = session_id
        self.timestamp = timestamp
        self.content = content
        self.context = context
        self.outcome = outcome
        self.importance = importance
        self.metadata = metadata or {}


class EpisodicMemory(BaseMemory):
    """情景记忆实现

    特点：
    - 存储具体的交互事件
    - 包含丰富的上下文信息
    - 按时间序列组织
    - 支持模式识别和回溯
    """

    def __init__(self, config: MemoryConfig, storage_backend=None):
        super().__init__(config, storage_backend)

        # 本地缓存（内存）
        self.episodes: List[Episode] = []
        self.sessions: Dict[str, List[str]] = {}  # session_id -> episode_ids

        # 模式识别缓存
        self.patterns_cache = {}
        self.last_pattern_analysis = None

        # 权威文档存储（SQLite）
        db_dir = self.config.storage_path if hasattr(self.config, 'storage_path') else "./memory_data"
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "memory.db")
        self.doc_store = SQLiteDocumentStore(db_path=db_path)

        # 统一嵌入模型（多语言，默认384维）
        self.embedder = get_text_embedder()

        # 获取数据库配置
        db_config = get_database_config()

        # 初始化Qdrant向量数据库（使用连接管理器避免重复连接）
        qdrant_config = db_config.get_qdrant_config() or {}
        qdrant_config["vector_size"] = get_dimension()
        self.vector_store = QdrantConnectionManager.get_instance(**qdrant_config)
        log.success(f"🎉 Episodic Memory Initialized! db_path={db_path}")

    def _to_json_safe_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """转换为SQLite JSON properties可保存的元数据。"""
        def convert(value):
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, dict):
                return {key: convert(item) for key, item in value.items()}
            if isinstance(value, (list, tuple, set)):
                return [convert(item) for item in value]
            return str(value)

        return convert(metadata or {})

    def add(self, memory_item: MemoryItem) -> str:
        """添加情景记忆"""
        log.info(
            f"📝 EpisodicMemory add start: id={memory_item.id}, user={memory_item.user_id}, "
            f"importance={memory_item.importance:.2f}, metadata_keys={list(memory_item.metadata.keys())}"
        )
        # 从元数据中提取情景信息，并保留调用方传入的完整metadata
        episode_metadata = dict(memory_item.metadata or {})
        session_id = episode_metadata.get("session_id", "default_session")
        context = episode_metadata.get("context") or {}
        outcome = episode_metadata.get("outcome")
        participants = episode_metadata.get("participants") or []
        tags = episode_metadata.get("tags") or []
        episode_metadata.update({
            "session_id": session_id,
            "context": context,
            "outcome": outcome,
            "participants": participants,
            "tags": tags
        })

        # 创建情景（内存缓存）
        episode = Episode(
            episode_id=memory_item.id,
            user_id=memory_item.user_id,
            session_id=session_id,
            timestamp=memory_item.timestamp,
            content=memory_item.content,
            context=context,
            outcome=outcome,
            importance=memory_item.importance,
            metadata=episode_metadata
        )
        self.episodes.append(episode)
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(episode.episode_id)
        log.debug(
            f"📦 EpisodicMemory cached episode: id={episode.episode_id}, "
            f"session={session_id}, session_size={len(self.sessions[session_id])}"
        )

        # 1) 权威存储（SQLite）
        ts_int = int(memory_item.timestamp.timestamp())
        log.debug(f"💾 EpisodicMemory SQLite add start: id={memory_item.id}, ts={ts_int}")
        self.doc_store.add_memory(
            memory_id=memory_item.id,
            user_id=memory_item.user_id,
            content=memory_item.content,
            memory_type="episodic",
            timestamp=ts_int,
            importance=memory_item.importance,
            properties=self._to_json_safe_metadata(episode_metadata)
        )
        log.info(f"✅ EpisodicMemory SQLite add done: id={memory_item.id}")

        # 2) 向量索引（Qdrant）
        try:
            log.debug(f"🧲 EpisodicMemory vector add start: id={memory_item.id}")
            embedding = self.embedder.encode(memory_item.content)
            if hasattr(embedding, "tolist"):
                embedding = embedding.tolist()
            self.vector_store.add_vectors(
                vectors=[embedding],
                metadata=[{
                    "memory_id": memory_item.id,
                    "user_id": memory_item.user_id,
                    "memory_type": "episodic",
                    "importance": memory_item.importance,
                    "session_id": session_id,
                    "content": memory_item.content
                }],
                ids=[memory_item.id]
            )
            log.info(f"✅ EpisodicMemory vector add done: id={memory_item.id}, dim={len(embedding)}")
        except Exception as e:
            # 向量入库失败不影响权威存储
            log.warn(f"⚠️ EpisodicMemory vector add failed, SQLite kept: id={memory_item.id}, error={e}")

        log.success(f"✅ EpisodicMemory add done: id={memory_item.id}, session={session_id}")
        return memory_item.id

    def retrieve(self, query: str, limit: int = 5, **kwargs) -> List[MemoryItem]:
        """检索情景记忆（结构化过滤 + 语义向量检索）"""
        user_id = kwargs.get("user_id")
        session_id = kwargs.get("session_id")
        time_range: Optional[Tuple[datetime, datetime]] = kwargs.get("time_range")
        min_importance: Optional[float] = kwargs.get("min_importance")
        log.info(
            f"🔍 EpisodicMemory retrieve start: query_len={len(query)}, limit={limit}, "
            f"user_id={user_id}, session_id={session_id}, min_importance={min_importance}, "
            f"time_range={time_range}"
        )

        # 结构化过滤候选（来自权威库）
        candidate_ids: Optional[set] = None
        if time_range is not None or min_importance is not None:
            start_ts = int(time_range[0].timestamp()) if time_range else None
            end_ts = int(time_range[1].timestamp()) if time_range else None
            docs = self.doc_store.search_memories(
                user_id=user_id,
                memory_type="episodic",
                start_time=start_ts,
                end_time=end_ts,
                min_importance=min_importance,
                limit=1000
            )
            candidate_ids = {d["memory_id"] for d in docs}
            log.info(f"🎯 EpisodicMemory structured candidates: count={len(candidate_ids)}")

        # 向量检索（Qdrant）
        try:
            log.debug("🔍 EpisodicMemory vector search start")
            query_vec = self.embedder.encode(query)
            if hasattr(query_vec, "tolist"):
                query_vec = query_vec.tolist()
            where = {"memory_type": "episodic"}
            if user_id:
                where["user_id"] = user_id
            hits = self.vector_store.search_similar(
                query_vector=query_vec,
                limit=max(limit * 5, 20),
                where=where
            )
            log.info(f"✅ EpisodicMemory vector search done: hits={len(hits)}")
        except Exception as e:
            hits = []
            log.warn(f"⚠️ EpisodicMemory vector search failed, fallback may run: {e}")

        # 过滤与重排
        now_ts = int(datetime.now().timestamp())
        results: List[Tuple[float, MemoryItem]] = []
        seen = set()
        for hit in hits:
            meta = hit.get("metadata", {})
            mem_id = meta.get("memory_id")
            if not mem_id or mem_id in seen:
                continue

            # 检查是否已遗忘
            episode = next((e for e in self.episodes if e.episode_id == mem_id), None)
            if episode and episode.context.get("forgotten", False):
                continue  # 跳过已遗忘的记忆

            if candidate_ids is not None and mem_id not in candidate_ids:
                continue
            if session_id and meta.get("session_id") != session_id:
                continue

            # 从权威库读取完整记录
            doc = self.doc_store.get_memory(mem_id)
            if not doc:
                continue

            # 计算综合分数：向量0.6 + 近因0.2 + 重要性0.2
            vec_score = float(hit.get("score", 0.0))
            age_days = max(0.0, (now_ts - int(doc["timestamp"])) / 86400.0)
            recency_score = 1.0 / (1.0 + age_days)
            imp = float(doc.get("importance", 0.5))

            # 新评分算法：向量检索纯基于相似度，重要性作为加权因子
            # 基础相似度得分（不受重要性影响）
            base_relevance = vec_score * 0.8 + recency_score * 0.2

            # 重要性作为乘法加权因子，范围 [0.8, 1.2]
            importance_weight = 0.8 + (imp * 0.4)

            # 最终得分：相似度 * 重要性权重
            combined = base_relevance * importance_weight
            log.info(f"""🧮 EpisodicMemory{doc}
            \t (1) final_score({combined:.2f})=base_relevance({base_relevance:.2f})*importance_weight({importance_weight:.2f})
            \t (2) importance_weight({importance_weight:.2f})=0.8 + importance({imp:.2f})*0.4
            \t (3) base_relevance({base_relevance:.2f}) = vector_score({vec_score:.2f})*0.8 + recency_score({recency_score:.2f})*0.2
            \t (4) recency_score({recency_score:.2f}) = 1 / (1 + age_days({age_days:.2f}))""")

            item = MemoryItem(
                id=doc["memory_id"],
                content=doc["content"],
                memory_type=doc["memory_type"],
                user_id=doc["user_id"],
                timestamp=datetime.fromtimestamp(doc["timestamp"]),
                importance=doc.get("importance", 0.5),
                metadata={
                    **doc.get("properties", {}),
                    "relevance_score": combined,
                    "vector_score": vec_score,
                    "recency_score": recency_score
                }
            )
            results.append((combined, item))
            seen.add(mem_id)

        # 若向量检索无结果，回退到简单关键词匹配（内存缓存）
        if not results:
            log.info(f"🔁 EpisodicMemory fallback keyword search start: cached={len(self.episodes)}")
            fallback = super()._generate_id  # 占位以避免未使用警告
            query_lower = query.lower()
            for ep in self._filter_episodes(user_id, session_id, time_range):
                if query_lower in ep.content.lower():
                    age_days = max(0.0, (now_ts - int(ep.timestamp.timestamp())) / 86400.0)
                    recency_score = 1.0 / (1.0 + age_days)
                    # 回退匹配：新评分算法
                    keyword_score = 0.5  # 简单关键词匹配的基础分数
                    base_relevance = keyword_score * 0.8 + recency_score * 0.2
                    importance_weight = 0.8 + (ep.importance * 0.4)
                    combined = base_relevance * importance_weight
                    log.info(f"""🧮 EpisodicMemory fallback{ep.__dict__}
                    \t (1) final_score({combined:.2f})=base_relevance({base_relevance:.2f})*importance_weight({importance_weight:.2f})
                    \t (2) importance_weight({importance_weight:.2f})=0.8 + episode.importance({ep.importance:.2f})*0.4
                    \t (3) base_relevance({base_relevance:.2f}) = keyword_score({keyword_score:.2f})*0.8 + recency_score({recency_score:.2f})*0.2
                    \t (4) recency_score({recency_score:.2f}) = 1 / (1 + age_days({age_days:.2f}))""")
                    item = MemoryItem(
                        id=ep.episode_id,
                        content=ep.content,
                        memory_type="episodic",
                        user_id=ep.user_id,
                        timestamp=ep.timestamp,
                        importance=ep.importance,
                        metadata={
                            "session_id": ep.session_id,
                            "context": ep.context,
                            "outcome": ep.outcome,
                            "relevance_score": combined
                        }
                    )
                    results.append((combined, item))

        results.sort(key=lambda x: x[0], reverse=True)
        final_results = [it for _, it in results[:limit]]
        log.success(f"✅ EpisodicMemory retrieve done: ranked={len(results)}, returned={len(final_results)}")
        return final_results


    def update(
        self,
        memory_id: str,
        content: str = None,
        importance: float = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """更新情景记忆（SQLite为权威，Qdrant按需重嵌入）"""
        log.info(
            f"🛠️ EpisodicMemory update start: id={memory_id}, has_content={content is not None}, "
            f"importance={importance}, metadata_keys={list((metadata or {}).keys())}"
        )
        updated = False
        for episode in self.episodes:
            if episode.episode_id == memory_id:
                if content is not None:
                    episode.content = content
                if importance is not None:
                    episode.importance = importance
                if metadata is not None:
                    if not hasattr(episode, "metadata"):
                        episode.metadata = {
                            "session_id": episode.session_id,
                            "context": episode.context,
                            "outcome": episode.outcome
                        }
                    episode.metadata.update(metadata)
                    episode.context.update(metadata.get("context") or {})
                    episode.metadata["context"] = episode.context
                    if "outcome" in metadata:
                        episode.outcome = metadata["outcome"]
                    episode.metadata["outcome"] = episode.outcome
                    episode.metadata.setdefault("session_id", episode.session_id)
                updated = True
                break
        log.debug(f"📦 EpisodicMemory cache update done: id={memory_id}, updated={updated}")

        # 更新SQLite
        doc_updated = self.doc_store.update_memory(
            memory_id=memory_id,
            content=content,
            importance=importance,
            properties=self._to_json_safe_metadata(metadata) if metadata is not None else None
        )
        log.info(f"💾 EpisodicMemory SQLite update done: id={memory_id}, updated={doc_updated}")

        # 如内容变更，重嵌入并upsert到Qdrant
        if content is not None:
            try:
                log.debug(f"🧲 EpisodicMemory vector update start: id={memory_id}")
                embedding = self.embedder.encode(content)
                if hasattr(embedding, "tolist"):
                    embedding = embedding.tolist()
                # 获取更新后的记录以同步payload
                doc = self.doc_store.get_memory(memory_id)
                payload = {
                    "memory_id": memory_id,
                    "user_id": doc["user_id"] if doc else "",
                    "memory_type": "episodic",
                    "importance": (doc.get("importance") if doc else importance) or 0.5,
                    "session_id": (doc.get("properties", {}) or {}).get("session_id"),
                    "content": content
                }
                self.vector_store.add_vectors(
                    vectors=[embedding],
                    metadata=[payload],
                    ids=[memory_id]
                )
                log.info(f"✅ EpisodicMemory vector update done: id={memory_id}, dim={len(embedding)}")
            except Exception as e:
                log.warn(f"⚠️ EpisodicMemory vector update failed: id={memory_id}, error={e}")

        result = updated or doc_updated
        log.success(f"✅ EpisodicMemory update done: id={memory_id}, updated={result}")
        return result

    def remove(self, memory_id: str) -> bool:
        """删除情景记忆（SQLite + Qdrant）"""
        log.info(f"🧹 EpisodicMemory remove start: id={memory_id}, cached={len(self.episodes)}")
        removed = False
        for i, episode in enumerate(self.episodes):
            if episode.episode_id == memory_id:
                removed_episode = self.episodes.pop(i)
                session_id = removed_episode.session_id
                if session_id in self.sessions:
                    self.sessions[session_id].remove(memory_id)
                    if not self.sessions[session_id]:
                        del self.sessions[session_id]
                removed = True
                break
        log.debug(f"📦 EpisodicMemory cache remove done: id={memory_id}, removed={removed}")

        # 权威库删除
        doc_deleted = self.doc_store.delete_memory(memory_id)
        log.info(f"💾 EpisodicMemory SQLite delete done: id={memory_id}, deleted={doc_deleted}")

        # 向量库删除
        try:
            self.vector_store.delete_memories([memory_id])
            log.info(f"✅ EpisodicMemory vector delete done: id={memory_id}")
        except Exception as e:
            log.warn(f"⚠️ EpisodicMemory vector delete failed: id={memory_id}, error={e}")

        result = removed or doc_deleted
        log.success(f"✅ EpisodicMemory remove done: id={memory_id}, removed={result}")
        return result

    def has_memory(self, memory_id: str) -> bool:
        """检查记忆是否存在"""
        # 检查内存缓存即可， 已经保证一致性
        return any(episode.episode_id == memory_id for episode in self.episodes)

    def clear(self):
        """清空所有情景记忆（仅清理episodic，不影响其他类型）"""
        log.info(f"🧹 EpisodicMemory clear start: cached={len(self.episodes)}")
        # 内存缓存
        self.episodes.clear()
        self.sessions.clear()
        self.patterns_cache.clear()

        # SQLite内的episodic全部删除
        docs = self.doc_store.search_memories(memory_type="episodic", limit=10000)
        ids = [d["memory_id"] for d in docs]
        log.info(f"💾 EpisodicMemory clear SQLite ids: count={len(ids)}")
        for mid in ids:
            self.doc_store.delete_memory(mid)

        # Qdrant按ID删除对应向量
        try:
            if ids:
                self.vector_store.delete_memories(ids)
                log.info(f"✅ EpisodicMemory clear vector done: count={len(ids)}")
        except Exception as e:
            log.warn(f"⚠️ EpisodicMemory clear vector failed: {e}")
        log.success("✅ EpisodicMemory clear done")

    def forget(self, strategy: str = "importance_based", threshold: float = 0.1, max_age_days: int = 30) -> int:
        """情景记忆遗忘机制（硬删除）"""
        log.info(
            f"🧹 EpisodicMemory forget start: strategy={strategy}, threshold={threshold}, "
            f"max_age_days={max_age_days}, count={len(self.episodes)}"
        )
        forgotten_count = 0
        current_time = datetime.now()

        to_remove = []  # 收集要删除的记忆ID

        for episode in self.episodes:
            should_forget = False

            if strategy == "importance_based":
                # 基于重要性遗忘
                if episode.importance < threshold:
                    should_forget = True
            elif strategy == "time_based":
                # 基于时间遗忘
                cutoff_time = current_time - timedelta(days=max_age_days)
                if episode.timestamp < cutoff_time:
                    should_forget = True
            elif strategy == "capacity_based":
                # 基于容量遗忘（保留最重要的）
                if len(self.episodes) > self.config.max_capacity:
                    sorted_episodes = sorted(self.episodes, key=lambda e: e.importance)
                    excess_count = len(self.episodes) - self.config.max_capacity
                    if episode in sorted_episodes[:excess_count]:
                        should_forget = True

            if should_forget:
                to_remove.append(episode.episode_id)

        # 执行硬删除
        for episode_id in to_remove:
            if self.remove(episode_id):
                forgotten_count += 1
                log.success(f"情景记忆硬删除: {episode_id[:8]}... (策略: {strategy})")

        log.success(f"✅ EpisodicMemory forget done: candidates={len(to_remove)}, forgotten={forgotten_count}")
        return forgotten_count

    def get_all(self) -> List[MemoryItem]:
        """获取所有情景记忆（转换为MemoryItem格式）"""
        log.debug(f"📦 EpisodicMemory get_all start: count={len(self.episodes)}")
        memory_items = []
        for episode in self.episodes:
            metadata = {
                "session_id": episode.session_id,
                "context": episode.context,
                "outcome": episode.outcome,
                **getattr(episode, "metadata", {})
            }
            memory_item = MemoryItem(
                id=episode.episode_id,
                content=episode.content,
                memory_type="episodic",
                user_id=episode.user_id,
                timestamp=episode.timestamp,
                importance=episode.importance,
                metadata=metadata
            )
            memory_items.append(memory_item)
        return memory_items

    def get_stats(self) -> Dict[str, Any]:
        """获取情景记忆统计信息（合并SQLite与Qdrant）"""
        log.debug("📊 EpisodicMemory stats start")
        # 硬删除模式：所有episodes都是活跃的
        active_episodes = self.episodes

        db_stats = self.doc_store.get_database_stats()
        try:
            vs_stats = self.vector_store.get_collection_stats()
        except Exception:
            vs_stats = {"store_type": "qdrant"}
        return {
            "count": len(active_episodes),  # 活跃记忆数量
            "forgotten_count": 0,  # 硬删除模式下已遗忘的记忆会被直接删除
            "total_count": len(self.episodes),  # 总记忆数量
            "sessions_count": len(self.sessions),
            "avg_importance": sum(e.importance for e in active_episodes) / len(
                active_episodes) if active_episodes else 0.0,
            "time_span_days": self._calculate_time_span(),
            "memory_type": "episodic",
            "vector_store": vs_stats,
            "document_store": {k: v for k, v in db_stats.items() if
                               k.endswith("_count") or k in ["store_type", "db_path"]}
        }

    def _calculate_time_span(self) -> float:
        """计算记忆时间跨度（天）"""
        if not self.episodes:
            return 0.0

        timestamps = [e.timestamp for e in self.episodes]
        min_time = min(timestamps)
        max_time = max(timestamps)

        return (max_time - min_time).days

    def get_session_episodes(self, session_id: str) -> List[Episode]:
        """获取指定会话的所有情景"""
        if session_id not in self.sessions:
            return []

        episode_ids = self.sessions[session_id]
        return [e for e in self.episodes if e.episode_id in episode_ids]

    def find_patterns(self, user_id: str = None, min_frequency: int = 2) -> List[Dict[str, Any]]:
        """发现用户行为模式"""
        # 检查缓存
        cache_key = f"{user_id}_{min_frequency}"
        if (cache_key in self.patterns_cache and
                self.last_pattern_analysis and
                (datetime.now() - self.last_pattern_analysis).hours < 1):
            return self.patterns_cache[cache_key]

        # 过滤情景
        episodes = [e for e in self.episodes if user_id is None or e.user_id == user_id]

        # 简单的模式识别：基于内容关键词
        keyword_patterns = {}
        context_patterns = {}

        for episode in episodes:
            # 提取关键词
            words = episode.content.lower().split()
            for word in words:
                if len(word) > 3:  # 忽略短词
                    keyword_patterns[word] = keyword_patterns.get(word, 0) + 1

            # 提取上下文模式
            for key, value in episode.context.items():
                pattern_key = f"{key}:{value}"
                context_patterns[pattern_key] = context_patterns.get(pattern_key, 0) + 1

        # 筛选频繁模式
        patterns = []

        for keyword, frequency in keyword_patterns.items():
            if frequency >= min_frequency:
                patterns.append({
                    "type": "keyword",
                    "pattern": keyword,
                    "frequency": frequency,
                    "confidence": frequency / len(episodes)
                })

        for context_pattern, frequency in context_patterns.items():
            if frequency >= min_frequency:
                patterns.append({
                    "type": "context",
                    "pattern": context_pattern,
                    "frequency": frequency,
                    "confidence": frequency / len(episodes)
                })

        # 按频率排序
        patterns.sort(key=lambda x: x["frequency"], reverse=True)

        # 缓存结果
        self.patterns_cache[cache_key] = patterns
        self.last_pattern_analysis = datetime.now()

        return patterns

    def get_timeline(self, user_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取时间线视图"""
        episodes = [e for e in self.episodes if user_id is None or e.user_id == user_id]
        episodes.sort(key=lambda x: x.timestamp, reverse=True)

        timeline = []
        for episode in episodes[:limit]:
            timeline.append({
                "episode_id": episode.episode_id,
                "timestamp": episode.timestamp.isoformat(),
                "content": episode.content[:100] + "..." if len(episode.content) > 100 else episode.content,
                "session_id": episode.session_id,
                "importance": episode.importance,
                "outcome": episode.outcome
            })

        return timeline

    def _filter_episodes(
        self,
        user_id: str = None,
        session_id: str = None,
        time_range: Tuple[datetime, datetime] = None
    ) -> List[Episode]:
        """过滤情景"""
        filtered = self.episodes

        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]

        if session_id:
            filtered = [e for e in filtered if e.session_id == session_id]

        if time_range:
            start_time, end_time = time_range
            filtered = [e for e in filtered if start_time <= e.timestamp <= end_time]

        return filtered

    def _persist_episode(self, episode: Episode):
        """持久化情景到存储后端"""
        if self.storage and hasattr(self.storage, 'add_memory'):
            self.storage.add_memory(
                memory_id=episode.episode_id,
                user_id=episode.user_id,
                content=episode.content,
                memory_type="episodic",
                timestamp=int(episode.timestamp.timestamp()),
                importance=episode.importance,
                properties={
                    "session_id": episode.session_id,
                    "context": episode.context,
                    "outcome": episode.outcome
                }
            )

    def _remove_from_storage(self, memory_id: str):
        """从存储后端删除"""
        if self.storage and hasattr(self.storage, 'delete_memory'):
            self.storage.delete_memory(memory_id)
