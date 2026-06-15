import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from josie_agents.memory.base import MemoryConfig, MemoryItem
import josie_agents.utils.log as log
from josie_agents.memory.types.episodic import EpisodicMemory
from josie_agents.memory.types.perceptual import PerceptualMemory
from josie_agents.memory.types.semantic import SemanticMemory
from josie_agents.memory.types.working import WorkingMemory


class MemoryManager:
    """记忆管理器 - 统一的记忆操作接口

    负责：
    - 记忆生命周期管理
    - 记忆优先级和重要性评估
    - 记忆遗忘和清理机制
    - 多类型记忆的协调管理
    """

    def __init__(
        self,
        config: Optional[MemoryConfig]=None,
        user_id: str = "default_user",
        enable_working: bool = True,
        enable_episodic: bool = True,
        enable_semantic: bool = True,
        enable_perceptual: bool = False
    ):
        self.config = config or MemoryConfig()
        self.user_id = user_id
        log.info(
            f"🧠 MemoryManager开始初始化: user_id={self.user_id}, "
            f"working={enable_working}, episodic={enable_episodic}, "
            f"semantic={enable_semantic}, perceptual={enable_perceptual}"
        )

        # 存储和检索功能已移至各记忆类型内部实现

        # 初始化各类型记忆
        self.memory_types = {}

        if enable_working:
            log.debug("🧠 初始化 working memory")
            self.memory_types['working'] = WorkingMemory(self.config)

        if enable_episodic:
            log.debug("🧠 初始化 episodic memory")
            self.memory_types['episodic'] = EpisodicMemory(self.config)

        if enable_semantic:
            log.debug("🧠 初始化 semantic memory")
            self.memory_types['semantic'] = SemanticMemory(self.config)

        if enable_perceptual:
            log.debug("🧠 初始化 perceptual memory")
            self.memory_types['perceptual'] = PerceptualMemory(self.config)

        log.success(f"🎉 MemoryManager初始化完成，启用记忆类型: {list(self.memory_types.keys())}")


    def add_memory(
        self,
        content: str,
        memory_type: str = "working",
        importance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_classify: bool = True
    ) -> str:
        """添加记忆

        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性分数 (0-1)
            metadata: 元数据
            auto_classify: 是否自动分类到合适的记忆类型

        Returns:
        记忆ID
        """
        log.info(
            f"📝 开始添加记忆: requested_type={memory_type}, auto_classify={auto_classify}, "
            f"content_len={len(content)}, metadata_keys={list((metadata or {}).keys())}"
        )

        # 自动分类记忆类型
        if auto_classify:
            requested_type = memory_type
            memory_type = self._classify_memory_type(content, metadata)
            log.debug(f"🏷️ 记忆类型自动分类: {requested_type} -> {memory_type}")

        # 计算重要性
        if importance is None:
            importance = self._calculate_importance(content, metadata)
            log.debug(f"🧮 自动计算记忆重要性: {importance:.2f}")
        else:
            log.debug(f"🧮 使用传入记忆重要性: {importance:.2f}")

        # 创建记忆项
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            content=content,
            memory_type=memory_type,
            user_id=self.user_id,
            timestamp=metadata.get('timestamp') or datetime.now(),
            importance=importance,
            metadata=metadata or {}
        )
        log.debug(f"📦 记忆项创建完成: id={memory_item.id}, type={memory_item.memory_type}, user={memory_item.user_id}")

        # 添加到对应的记忆类型
        if memory_type in self.memory_types:
            log.info(f"📤 分发记忆到 {memory_type}: id={memory_item.id}")
            memory_id = self.memory_types[memory_type].add(memory_item)
            log.success(f"✅ 添加记忆到 {memory_type}: {memory_id}")
            return memory_id
        else:
            log.error(f"❌ 添加记忆失败，不支持的记忆类型: {memory_type}, enabled={list(self.memory_types.keys())}")
            raise ValueError(f"不支持的记忆类型: {memory_type}")

    def retrieve_memories(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10,
        min_importance: float = 0.0,
        time_range: Optional[tuple] = None
    ) -> List[MemoryItem]:
        """检索记忆

        Args:
            query: 查询内容
            memory_types: 要检索的记忆类型列表
            limit: 返回数量限制
            min_importance: 最小重要性阈值
            time_range: 时间范围 (start_time, end_time)

        Returns:
            检索到的记忆列表
        """
        if memory_types is None:
            memory_types = list(self.memory_types.keys())

        log.info(
            f"🔍 开始检索记忆: query_len={len(query)}, memory_types={memory_types}, "
            f"limit={limit}, min_importance={min_importance}, time_range={time_range}"
        )

        # 从各个记忆类型中检索
        all_results = []
        per_type_limit = max(1, limit // len(memory_types))
        log.debug(f"📏 每类记忆检索上限: {per_type_limit}")

        for memory_type in memory_types:
            if memory_type in self.memory_types:
                memory_instance = self.memory_types[memory_type]
                try:
                    log.debug(f"🔎 开始检索 {memory_type} 记忆")
                    # 使用各个记忆类型自己的检索方法
                    type_results = memory_instance.retrieve(
                        query=query,
                        limit=per_type_limit,
                        min_importance=min_importance,
                        user_id=self.user_id,
                        time_range=time_range
                    )
                    all_results.extend(type_results)
                    log.info(f"✅ {memory_type} 记忆检索完成: results={len(type_results)}")
                except Exception as e:
                    log.warn(f"⚠️ 检索 {memory_type} 记忆时出错: {e}")
                    continue
            else:
                log.warn(f"⏭️ 跳过未启用记忆类型: {memory_type}")

        # 按重要性和相关性排序
        all_results.sort(key=lambda x: x.importance, reverse=True)
        results = all_results[:limit]
        log.success(f"✅ 记忆检索完成: merged={len(all_results)}, returned={len(results)}")
        return results

    def update_memory(
            self,
            memory_id: str,
            content: Optional[str] = None,
            importance: Optional[float] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新记忆

        Args:
            memory_id: 记忆ID
            content: 新内容
            importance: 新重要性
            metadata: 新元数据

        Returns:
            是否更新成功
        """
        log.info(
            f"🛠️ 开始更新记忆: id={memory_id}, has_content={content is not None}, "
            f"importance={importance}, metadata_keys={list((metadata or {}).keys())}"
        )
        # 查找记忆所在的类型
        for memory_type, memory_instance in self.memory_types.items():
            if memory_instance.has_memory(memory_id):
                log.debug(f"🎯 更新命中记忆类型: {memory_type}, id={memory_id}")
                updated = memory_instance.update(memory_id, content, importance, metadata)
                log.info(f"✅ 更新记忆完成: id={memory_id}, type={memory_type}, updated={updated}")
                return updated

        log.error(f"❌ 未找到记忆: {memory_id}")
        return False

    def remove_memory(self, memory_id: str) -> bool:
        """删除记忆

        Args:
            memory_id: 记忆ID

        Returns:
            是否删除成功
        """
        log.info(f"🧹 开始删除记忆: id={memory_id}")
        for memory_type, memory_instance in self.memory_types.items():
            if memory_instance.has_memory(memory_id):
                log.debug(f"🎯 删除命中记忆类型: {memory_type}, id={memory_id}")
                removed = memory_instance.remove(memory_id)
                log.info(f"✅ 删除记忆完成: id={memory_id}, type={memory_type}, removed={removed}")
                return removed

        log.error(f"❌ 未找到记忆: {memory_id}")
        return False

    def forget_memories(
            self,
            strategy: str = "importance_based",
            threshold: float = 0.1,
            max_age_days: int = 30
    ) -> int:
        """记忆遗忘机制

        Args:
            strategy: 遗忘策略 ("importance_based", "time_based", "capacity_based")
            threshold: 遗忘阈值
            max_age_days: 最大保存天数

        Returns:
            遗忘的记忆数量
        """
        log.info(f"🧹 开始执行记忆遗忘: strategy={strategy}, threshold={threshold}, max_age_days={max_age_days}")
        total_forgotten = 0

        for memory_type, memory_instance in self.memory_types.items():
            if hasattr(memory_instance, 'forget'):
                log.debug(f"🧹 执行 {memory_type} 遗忘")
                forgotten = memory_instance.forget(strategy, threshold, max_age_days)
                total_forgotten += forgotten
                log.info(f"✅ {memory_type} 遗忘完成: forgotten={forgotten}")
            else:
                log.warn(f"⚠️ {memory_type} 不支持遗忘接口")

        log.info(f"✅ 记忆遗忘完成: {total_forgotten} 条记忆")
        return total_forgotten

    def consolidate_memories(
        self,
        from_type: str = "working",
        to_type: str = "episodic",
        importance_threshold: float = 0.7
    ) -> int:
        """记忆整合 - 将重要的短期记忆转换为长期记忆

        Args:
            from_type: 源记忆类型
            to_type: 目标记忆类型
            importance_threshold: 重要性阈值

        Returns:
            整合的记忆数量
        """
        log.info(
            f"🔁 开始记忆整合: from={from_type}, to={to_type}, "
            f"importance_threshold={importance_threshold}"
        )
        if from_type not in self.memory_types or to_type not in self.memory_types:
            log.error(f"❌ 记忆类型不存在: {from_type} -> {to_type}")
            return 0

        # 获取高重要性的源记忆
        source_memory = self.memory_types[from_type]
        target_memory = self.memory_types[to_type]

        # 获取需要整合的记忆
        all_memories = source_memory.get_all()
        candidates = [
            m for m in all_memories
            if m.importance >= importance_threshold
        ]
        log.info(f"🧩 记忆整合候选: total={len(all_memories)}, candidates={len(candidates)}")

        consolidated_count = 0
        for memory in candidates:
            # 移动到目标记忆类型
            if source_memory.remove(memory.id):
                memory.memory_type = to_type
                memory.importance *= 1.1  # 提升重要性
                target_memory.add(memory)
                consolidated_count += 1
                log.debug(f"✅ 记忆整合成功: id={memory.id}, {from_type}->{to_type}")
            else:
                log.warn(f"⚠️ 记忆整合移除源记忆失败: id={memory.id}, from={from_type}")

        log.success(f"✅ 记忆整合完成: {consolidated_count} 条记忆从 {from_type} 转移到 {to_type}")
        return consolidated_count

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        log.debug(f"📊 开始获取记忆统计: enabled={list(self.memory_types.keys())}")
        stats = {
            "user_id": self.user_id,
            "enabled_types": list(self.memory_types.keys()),
            "total_memories": 0,
            "memories_by_type": {},
            "config": {
                "max_capacity": self.config.max_capacity,
                "importance_threshold": self.config.importance_threshold,
                "decay_factor": self.config.decay_factor
            }
        }

        for memory_type, memory_instance in self.memory_types.items():
            type_stats = memory_instance.get_stats()
            stats["memories_by_type"][memory_type] = type_stats
            # 使用count字段（活跃记忆数），而不是total_count（包含已遗忘的）
            stats["total_memories"] += type_stats.get("count", 0)
            log.debug(f"📊 {memory_type} 统计: count={type_stats.get('count', 0)}")

        log.info(f"📊 记忆统计完成: total={stats['total_memories']}")
        return stats

    def clear_all_memories(self):
        """清空所有记忆"""
        log.info(f"🧹 开始清空所有记忆: types={list(self.memory_types.keys())}")
        for memory_type, memory_instance in self.memory_types.items():
            log.debug(f"🧹 清空 {memory_type} 记忆")
            memory_instance.clear()
        log.success("✅ 所有记忆已清空")

    def _classify_memory_type(self, content: str, metadata: Optional[Dict[str, Any]]) -> str:
        """自动分类记忆类型"""
        if metadata and metadata.get("type"):
            log.debug(f"🏷️ 使用metadata指定记忆类型: {metadata['type']}")
            return metadata["type"]

        # 简单的分类逻辑，可以扩展为更复杂的分类器
        if self._is_episodic_content(content):
            log.debug("🏷️ 内容命中情景记忆关键词")
            return "episodic"
        elif self._is_semantic_content(content):
            log.debug("🏷️ 内容命中语义记忆关键词")
            return "semantic"
        else:
            log.debug("🏷️ 内容未命中特殊关键词，归入working")
            return "working"

    def _is_episodic_content(self, content: str) -> bool:
        """判断是否为情景记忆内容"""
        episodic_keywords = ["昨天", "今天", "明天", "上次", "记得", "发生", "经历"]
        return any(keyword in content for keyword in episodic_keywords)

    def _is_semantic_content(self, content: str) -> bool:
        """判断是否为语义记忆内容"""
        semantic_keywords = ["定义", "概念", "规则", "知识", "原理", "方法"]
        return any(keyword in content for keyword in semantic_keywords)

    def _calculate_importance(self, content: str, metadata: Optional[Dict[str, Any]]) -> float:
        """计算记忆重要性"""
        importance = 0.5  # 基础重要性

        # 基于内容长度
        if len(content) > 100:
            importance += 0.1

        # 基于关键词
        important_keywords = ["重要", "关键", "必须", "注意", "警告", "错误"]
        if any(keyword in content for keyword in important_keywords):
            importance += 0.2

        # 基于元数据
        if metadata:
            if metadata.get("priority") == "high":
                importance += 0.3
            elif metadata.get("priority") == "low":
                importance -= 0.2

        final_importance = max(0.0, min(1.0, importance))
        log.debug(f"🧮 重要性计算完成: raw={importance:.2f}, final={final_importance:.2f}")
        return final_importance

    def __str__(self) -> str:
        stats = self.get_memory_stats()
        return f"MemoryManager(user={self.user_id}, total={stats['total_memories']})"
