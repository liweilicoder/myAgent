from datetime import datetime, timedelta
from typing import List, Dict, Any

from josie_agents.memory.base import BaseMemory, MemoryConfig, MemoryItem
import heapq
import josie_agents.utils.log as log

class WorkingMemory(BaseMemory):
    """工作记忆实现

    特点：
    - 容量有限（通常10-20条记忆）
    - 时效性强（会话级别）
    - 优先级管理
    - 自动清理过期记忆
    """

    def __init__(self, config: MemoryConfig, storage_backend=None):
        super().__init__(config, storage_backend)

        # 工作记忆特定配置
        self.max_capacity = self.config.working_memory_capacity
        self.max_tokens = self.config.working_memory_tokens
        # 纯内存TTL（分钟），可通过在 MemoryConfig 上挂载 working_memory_ttl_minutes 覆盖
        self.max_age_minutes = getattr(self.config, 'working_memory_ttl_minutes', 120)
        self.current_tokens = 0
        self.session_start = datetime.now()

        # 内存存储（工作记忆不需要持久化）
        self.memories: List[MemoryItem] = []

        # 使用优先级队列管理记忆
        self.memory_heap = []  # (priority, timestamp, memory_item)
        log.success(
            f"🎉 Working Memory Initialized! capacity={self.max_capacity}, "
            f"max_tokens={self.max_tokens}, ttl_minutes={self.max_age_minutes}"
        )

    def add(self, memory_item: MemoryItem) -> str:
        """添加工作记忆"""
        log.debug(
            f"📝 WorkingMemory add start: id={memory_item.id}, user={memory_item.user_id}, "
            f"importance={memory_item.importance:.2f}, count={len(self.memories)}, tokens={self.current_tokens}"
        )
        # 过期清理
        self._expire_old_memories()
        # 计算优先级（重要性 + 时间衰减）
        priority = self._calculate_priority(memory_item)
        log.debug(f"🧮 WorkingMemory priority calculated: id={memory_item.id}, priority={priority:.4f}")

        # heapq 小顶堆：存 (priority, timestamp, memory_item)，堆顶始终是优先级最低的记忆
        heapq.heappush(self.memory_heap, (priority, memory_item.timestamp, memory_item))
        self.memories.append(memory_item)

        # 更新token计数
        self.current_tokens += len(memory_item.content.split())

        # 检查容量限制
        self._enforce_capacity_limits()
        log.success(
            f"🌺 Working Memory Added Success: {memory_item}, "
            f"count={len(self.memories)}, tokens={self.current_tokens}"
        )
        return memory_item.id

    def retrieve(self, query: str, limit: int = 5, user_id: str = None, **kwargs) -> List[MemoryItem]:
        """检索工作记忆 - 混合语义向量检索和关键词匹配"""
        log.debug(
            f"🔍 WorkingMemory retrieve start: query=【{query}】, limit={limit}, "
            f"user_id={user_id}, total_memory_count={len(self.memories)}"
        )
        # 清理过期的记忆， 防止已经遗忘的记忆被召回
        self._expire_old_memories()
        if not self.memories:
            log.info("🕳️ WorkingMemory retrieve done: no memories")
            return []

        # 按用户ID过滤（如果提供）
        filtered_memories = self.memories
        if user_id:
            filtered_memories = [m for m in self.memories if m.user_id == user_id]
        log.debug(f"🎯 WorkingMemory filter by user_id done: before_filtered={len(self.memories)},after_filtered={len(filtered_memories)}")

        if not filtered_memories:
            log.info("🕳️ WorkingMemory retrieve done: no memories after user filter")
            return []

        # 尝试语义向量检索（如果有嵌入模型）
        vector_scores = {}
        try:
            # 简单的语义相似度计算（使用TF-IDF或其他轻量级方法）
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np

            # 准备文档
            documents = [query] + [m.content for m in filtered_memories]

            # 使用字符级 n-gram（1-4）避免中文无空格分词导致 word tokenizer
            # 把整段汉字识别为单一 token、与 query token 零交集的问题
            vectorizer = TfidfVectorizer(
                analyzer='char_wb',
                ngram_range=(1, 4),
                lowercase=True,
            )
            tfidf_matrix = vectorizer.fit_transform(documents)

            # 计算相似度
            query_vector = tfidf_matrix[0:1]
            doc_vectors = tfidf_matrix[1:]
            similarities = cosine_similarity(query_vector, doc_vectors).flatten()

            # 存储向量分数
            for i, memory in enumerate(filtered_memories):
                vector_scores[memory.id] = similarities[i]

        except Exception as e:
            # 如果向量检索失败，回退到关键词匹配
            vector_scores = {}
            log.warn(f"☹️vectorizer failed，back to keyword: {e}")

        # 计算最终分数
        query_lower = query.lower()
        scored_memories = []

        for memory in filtered_memories:
            content_lower = memory.content.lower()

            # 获取向量分数（如果有）
            vector_score = vector_scores.get(memory.id, 0.0)

            # 关键词匹配分数
            keyword_score = 0.0
            if query_lower in content_lower:
                keyword_score = len(query_lower) / len(content_lower)
            else:
                # 分词匹配
                query_words = set(query_lower.split())
                content_words = set(content_lower.split())
                intersection = query_words.intersection(content_words)
                if intersection:
                    keyword_score = len(intersection) / len(query_words.union(content_words)) * 0.8

            # 混合分数：向量检索 + 关键词匹配
            if vector_score > 0:
                base_relevance = vector_score * 0.7 + keyword_score * 0.3
            else:
                base_relevance = keyword_score

            # 时间衰减
            time_decay = self._calculate_time_decay(memory.timestamp)
            base_relevance *= time_decay

            # 重要性权重
            importance_weight = 0.8 + (memory.importance * 0.4)
            final_score = base_relevance * importance_weight
            log.info(f"""🧮 Memory{memory}
            \t (1) final_score({final_score:.2f})=base_relevance({base_relevance:.2f})*importance_weight({importance_weight:.2f})
            \t (2) importance_weight({importance_weight:.2f})=0.8 + memory.importance({memory.importance:.2f})*0.4
            \t (3) base_relevance({base_relevance:.2f}) = [vector_score({vector_score:.2f})*0.7 + keyword_score({keyword_score:.2f})*0.3] * time_decay({time_decay:.2f})""")

            if final_score > 0:
                scored_memories.append((final_score, memory))

        # 按分数排序并返回
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        results = [memory for _, memory in scored_memories[:limit]]
        log.success(f"✅ WorkingMemory retrieve done: scored={len(scored_memories)}, returned={len(results)}")
        return results

    def update(
        self,
        memory_id: str,
        content: str = None,
        importance: float = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """更新工作记忆"""
        log.info(
            f"🛠️ WorkingMemory update start: id={memory_id}, has_content={content is not None}, "
            f"importance={importance}, metadata_keys={list((metadata or {}).keys())}"
        )
        for memory in self.memories:
            if memory.id == memory_id:
                old_tokens = len(memory.content.split())

                if content is not None:
                    memory.content = content
                    # 更新token计数
                    new_tokens = len(content.split())
                    self.current_tokens = self.current_tokens - old_tokens + new_tokens

                if importance is not None:
                    memory.importance = importance

                if metadata is not None:
                    memory.metadata.update(metadata)

                # 重新计算优先级并更新堆
                self._update_heap_priority(memory)
                log.success(f"🎉 Working Memory Updated: {memory}")
                return True
        log.warn(f"⚠️ WorkingMemory update miss: id={memory_id}")
        return False

    def remove(self, memory_id: str) -> bool:
        """删除工作记忆"""
        log.debug(f"🧹 WorkingMemory remove start: id={memory_id}, count={len(self.memories)}")
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                removed_memory = self.memories.pop(i)

                # 更新token计数
                self.current_tokens -= len(removed_memory.content.split())
                self.current_tokens = max(0, self.current_tokens)
                log.success(f"🧹 Working Memory Removed: {removed_memory}")
                return True
        log.warn(f"⚠️ WorkingMemory remove miss: id={memory_id}")
        return False

    def has_memory(self, memory_id: str) -> bool:
        """检查记忆是否存在"""
        return any(memory.id == memory_id for memory in self.memories)

    def clear(self):
        """清空所有工作记忆"""
        log.info(f"🧹 WorkingMemory clear start: count={len(self.memories)}, tokens={self.current_tokens}")
        self.memories.clear()
        self.memory_heap.clear()
        self.current_tokens = 0
        log.success("✅ WorkingMemory clear done")

    def get_stats(self) -> Dict[str, Any]:
        """获取工作记忆统计信息"""
        log.debug("📊 WorkingMemory stats start")
        # 过期清理（惰性）
        self._expire_old_memories()

        # 工作记忆中的记忆都是活跃的（已遗忘的记忆会被直接删除）
        active_memories = self.memories

        return {
            "count": len(active_memories),  # 活跃记忆数量
            "forgotten_count": 0,  # 工作记忆中已遗忘的记忆会被直接删除
            "total_count": len(self.memories),  # 总记忆数量
            "current_tokens": self.current_tokens,
            "max_capacity": self.max_capacity,
            "max_tokens": self.max_tokens,
            "max_age_minutes": self.max_age_minutes,
            "session_duration_minutes": (datetime.now() - self.session_start).total_seconds() / 60,
            "avg_importance": sum(m.importance for m in active_memories) / len(
                active_memories) if active_memories else 0.0,
            "capacity_usage": len(active_memories) / self.max_capacity if self.max_capacity > 0 else 0.0,
            "token_usage": self.current_tokens / self.max_tokens if self.max_tokens > 0 else 0.0,
            "memory_type": "working"
        }

    def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """获取最近的记忆"""
        sorted_memories = sorted(
            self.memories,
            key=lambda x: x.timestamp,
            reverse=True
        )
        return sorted_memories[:limit]

    def get_important(self, limit: int = 10) -> List[MemoryItem]:
        """获取重要记忆"""
        sorted_memories = sorted(
            self.memories,
            key=lambda x: x.importance,
            reverse=True
        )
        return sorted_memories[:limit]


    def get_all(self) -> List[MemoryItem]:
        """获取所有记忆"""
        return self.memories.copy()

    def get_context_summary(self, max_length: int = 500) -> str:
        """获取上下文摘要"""
        if not self.memories:
            return "No working memories available."

        # 按重要性和时间排序
        sorted_memories = sorted(
            self.memories,
            key=lambda m: (m.importance, m.timestamp),
            reverse=True
        )

        summary_parts = []
        current_length = 0

        for memory in sorted_memories:
            content = memory.content
            if current_length + len(content) <= max_length:
                summary_parts.append(content)
                current_length += len(content)
            else:
                # 截断最后一个记忆
                remaining = max_length - current_length
                if remaining > 50:  # 至少保留50个字符
                    summary_parts.append(content[:remaining] + "...")
                break

        return "Working Memory Context:\n" + "\n".join(summary_parts)

    def forget(self, strategy: str = "importance_based", threshold: float = 0.1, max_age_days: int = 1) -> int:
        """工作记忆遗忘机制"""
        log.debug(
            f"🧹 WorkingMemory forget start: strategy={strategy}, threshold={threshold}, "
            f"max_age_days={max_age_days}, count={len(self.memories)}"
        )
        forgotten_count = 0
        current_time = datetime.now()

        to_remove = []

        # 始终先执行TTL过期（分钟级）
        cutoff_ttl = current_time - timedelta(minutes=self.max_age_minutes)
        for memory in self.memories:
            if memory.timestamp < cutoff_ttl:
                to_remove.append(memory.id)

        if strategy == "importance_based":
            # 删除低重要性记忆
            for memory in self.memories:
                if memory.importance < threshold:
                    to_remove.append(memory.id)

        elif strategy == "time_based":
            # 删除过期记忆（工作记忆通常以小时计算）
            cutoff_time = current_time - timedelta(hours=max_age_days * 24)
            for memory in self.memories:
                if memory.timestamp < cutoff_time:
                    to_remove.append(memory.id)

        elif strategy == "capacity_based":
            # 删除超出容量的记忆
            if len(self.memories) > self.max_capacity:
                # 按优先级排序，删除最低的
                sorted_memories = sorted(
                    self.memories,
                    key=lambda m: self._calculate_priority(m)
                )
                excess_count = len(self.memories) - self.max_capacity
                for memory in sorted_memories[:excess_count]:
                    to_remove.append(memory.id)

        # 执行删除
        for memory_id in to_remove:
            if self.remove(memory_id):
                forgotten_count += 1

        log.success(f"✅ WorkingMemory forget done: candidates={len(to_remove)}, forgotten={forgotten_count}")
        return forgotten_count

    def _calculate_priority(self, memory: MemoryItem) -> float:
        """计算记忆优先级"""
        # 基础优先级 = 重要性
        priority = memory.importance

        # 时间衰减
        time_decay = self._calculate_time_decay(memory.timestamp)
        priority *= time_decay

        return priority

    def _calculate_time_decay(self, timestamp: datetime) -> float:
        """计算时间衰减因子"""
        time_diff = datetime.now() - timestamp
        passed_hour_cnt = time_diff.total_seconds() / 3600

        # 指数衰减（工作记忆衰减更快）
        decay_factor = self.config.decay_factor ** passed_hour_cnt  # 每1h衰减
        return max(0.1, decay_factor)  # 最小保持10%的权重

    def _enforce_capacity_limits(self):
        """强制执行容量限制"""
        # 检查记忆数量限制
        while len(self.memories) > self.max_capacity:
            log.warn(f"⚠️ WorkingMemory count over capacity: count={len(self.memories)}, max={self.max_capacity}")
            self._remove_lowest_priority_memory()

        # 检查token限制
        while self.current_tokens > self.max_tokens:
            log.warn(f"⚠️ WorkingMemory tokens over capacity: tokens={self.current_tokens}, max={self.max_tokens}")
            self._remove_lowest_priority_memory()

    def _expire_old_memories(self):
        """按TTL清理过期记忆，并同步更新堆与token计数"""
        if not self.memories:
            return
        cutoff_time = datetime.now() - timedelta(minutes=self.max_age_minutes)
        # 过滤保留的记忆
        kept: List[MemoryItem] = []
        removed_token_sum = 0
        for m in self.memories:
            if m.timestamp >= cutoff_time:
                kept.append(m)
            else:
                log.info(f"⛰️ Expired Memory: {m} has been removed, cutoff time: {cutoff_time}")
                removed_token_sum += len(m.content.split())
        if len(kept) == len(self.memories):
            return
        # 覆盖列表与token
        removed_count = len(self.memories) - len(kept)
        self.memories = kept
        self.current_tokens = max(0, self.current_tokens - removed_token_sum)
        # 重建堆
        self.memory_heap = []
        for mem in self.memories:
            priority = self._calculate_priority(mem)
            heapq.heappush(self.memory_heap, (priority, mem.timestamp, mem))
        log.info(
            f"🧹 WorkingMemory expired cleanup done: removed={removed_count}, "
            f"remaining={len(self.memories)}, tokens={self.current_tokens}"
        )

    def _remove_lowest_priority_memory(self):
        """从堆顶取出优先级最低的记忆并删除；跳过堆中已失效的 stale 条目"""
        while self.memory_heap:
            priority, timestamp, memory = heapq.heappop(self.memory_heap)
            if self.has_memory(memory.id):
                log.debug(f"🧹 WorkingMemory remove lowest priority: id={memory.id}, priority={priority:.4f}")
                self.remove(memory.id)
                return
        log.warn("⚠️ WorkingMemory remove lowest priority skipped: heap empty")

    def _update_heap_priority(self, memory: MemoryItem):
        """更新堆中记忆的优先级（重建堆）"""
        log.debug(f"🔁 WorkingMemory heap rebuild start: trigger_id={memory.id}, count={len(self.memories)}")
        self.memory_heap = []
        for mem in self.memories:
            priority = self._calculate_priority(mem)
            heapq.heappush(self.memory_heap, (priority, mem.timestamp, mem))
        log.debug(f"✅ WorkingMemory heap rebuild done: heap_size={len(self.memory_heap)}")
