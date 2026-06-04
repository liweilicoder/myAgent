from datetime import datetime
from typing import Dict, Any, List, Optional

import numpy as np
import spacy
import josie_agents.utils.log as log

from josie_agents.core.database_config import get_database_config
from josie_agents.memory.base import BaseMemory, MemoryConfig, MemoryItem
from josie_agents.memory.embedding import get_text_embedder, get_dimension
from josie_agents.memory.storage.neo4j_store import Neo4jGraphStore
from josie_agents.memory.storage.qdrant_store import QdrantConnectionManager


class Entity:
    def __init__(
        self,
        entity_id: str,
        name: str,
        entity_type: str = "MISC",
        description: str = "",
        properties: Dict[str, Any] = None,
    ):
        self.entity_id = entity_id
        self.name = name
        self.entity_type = entity_type  # PERSON, ORG, PRODUCT, SKILL, CONCEPT等
        self.description = description
        self.properties = properties or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.frequency = 1  # 出现频率

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "properties": self.properties,
            "frequency": self.frequency
        }

class Relation:
    def __init__(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str,
        strength: float = 1.0,
        evidence: str = "",
        properties: Dict[str, Any] = None
    ):
        self.from_entity = from_entity
        self.to_entity = to_entity
        self.relation_type = relation_type
        self.strength = strength
        self.evidence = evidence  # 支持该关系的原文本
        self.properties = properties or {}
        self.created_at = datetime.now()
        self.frequency = 1  # 关系出现频率

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_entity": self.from_entity,
            "to_entity": self.to_entity,
            "relation_type": self.relation_type,
            "strength": self.strength,
            "evidence": self.evidence,
            "properties": self.properties,
            "frequency": self.frequency
        }

class SemanticMemory(BaseMemory):
    """增强语义记忆实现

    特点：
    - 使用HuggingFace中文预训练模型进行文本嵌入
    - 向量检索进行快速相似度匹配
    - 知识图谱存储实体和关系
    - 混合检索策略：向量+图+语义推理
    """

    def __init__(self, config: MemoryConfig, storage_backend=None):
        super().__init__(config, storage_backend)

        # 嵌入模型（统一提供）
        self.embedding_model = None
        self._init_embedding_model()

        # 专业数据库存储
        self.vector_store = None
        self.graph_store = None
        self._init_databases()

        # 实体和关系缓存 (用于快速访问)
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []

        # 实体识别器
        self.nlp = None
        self._init_nlp()

        # 记忆存储
        self.semantic_memories: List[MemoryItem] = []
        self.memory_embeddings: Dict[str, np.ndarray] = {}

        log.success("增强语义记忆初始化完成（使用Qdrant+Neo4j专业数据库）")

    def _init_embedding_model(self):
        """初始化统一嵌入模型（由 embedding_provider 管理）。"""
        try:
            self.embedding_model = get_text_embedder()
            # 轻量健康检查与日志
            try:
                test_vec = self.embedding_model.encode("health_check")
                dim = getattr(self.embedding_model, "dimension", len(test_vec))
                log.success(f"✅ 嵌入模型就绪，维度: {dim}")
            except Exception:
                log.success("✅ 嵌入模型就绪")
        except Exception as e:
            log.error(f"❌ 嵌入模型初始化失败: {e}")
            raise

    def _init_databases(self):
        """初始化专业数据库存储"""
        try:
            # 获取数据库配置
            db_config = get_database_config()

            # 初始化Qdrant向量数据库（使用连接管理器避免重复连接）
            qdrant_config = db_config.get_qdrant_config() or {}
            qdrant_config["vector_size"] = get_dimension()
            self.vector_store = QdrantConnectionManager.get_instance(**qdrant_config)
            log.success("✅ Qdrant向量数据库初始化完成")

            # 初始化Neo4j图数据库
            neo4j_config = db_config.get_neo4j_config()
            self.graph_store = Neo4jGraphStore(**neo4j_config)
            log.success("✅ Neo4j图数据库初始化完成")

            # 验证连接
            vector_health = self.vector_store.health_check()
            graph_health = self.graph_store.health_check()

            if not vector_health:
                log.warn("⚠️ Qdrant连接异常，部分功能可能受限")
            if not graph_health:
                log.warn("⚠️ Neo4j连接异常，图搜索功能可能受限")

            log.info(f"🏥 数据库健康状态: Qdrant={'✅' if vector_health else '❌'}, Neo4j={'✅' if graph_health else '❌'}")

        except Exception as e:
            log.error(f"❌ 数据库初始化失败: {e}")
            log.info("💡 请检查数据库配置和网络连接")
            log.info("💡 参考 DATABASE_SETUP_GUIDE.md 进行配置")
            raise

    def _init_nlp(self):
        """初始化NLP处理器 - 智能多语言支持"""
        try:
            self.nlp_models = {}

            # 尝试加载多语言模型
            models_to_try = [
                ("zh_core_web_sm", "中文"),
                ("en_core_web_sm", "英文")
            ]

            loaded_models = []
            for model_name, lang_name in models_to_try:
                try:
                    nlp = spacy.load(model_name)
                    self.nlp_models[model_name] = nlp
                    loaded_models.append(lang_name)
                    log.info(f"✅ 加载{lang_name}spaCy模型: {model_name}")
                except OSError:
                    log.warn(f"⚠️ {lang_name}spaCy模型不可用: {model_name}")

            # 设置主要NLP处理器
            if "zh_core_web_sm" in self.nlp_models:
                self.nlp = self.nlp_models["zh_core_web_sm"]
                log.info("🎯 主要使用中文spaCy模型")
            elif "en_core_web_sm" in self.nlp_models:
                self.nlp = self.nlp_models["en_core_web_sm"]
                log.info("🎯 主要使用英文spaCy模型")
            else:
                self.nlp = None
                log.warn("⚠️ 无可用spaCy模型，实体提取将受限")

            if loaded_models:
                log.info(f"📚 可用语言模型: {', '.join(loaded_models)}")

        except ImportError:
            log.warn("⚠️ spaCy不可用，实体提取将受限")
            self.nlp = None
            self.nlp_models = {}

    def add(self, memory_item: MemoryItem) -> str:
        """添加语义记忆"""
        try:
            # 1. 生成文本嵌入
            embedding = self.embedding_model.encode(memory_item.content)
            self.memory_embeddings[memory_item.id] = embedding

            # 2. 提取实体和关系
            entities = self._extract_entities(memory_item.content)
            relations = self._extract_relations(memory_item.content, entities)

            # 3. 存储到Neo4j图数据库
            for entity in entities:
                self._add_entity_to_graph(entity, memory_item)

            for relation in relations:
                self._add_relation_to_graph(relation, memory_item)

            # 4. 存储到Qdrant向量数据库
            metadata = {
                "memory_id": memory_item.id,
                "user_id": memory_item.user_id,
                "content": memory_item.content,
                "memory_type": memory_item.memory_type,
                "timestamp": int(memory_item.timestamp.timestamp()),
                "importance": memory_item.importance,
                "entities": [e.entity_id for e in entities],
                "entity_count": len(entities),
                "relation_count": len(relations)
            }

            success = self.vector_store.add_vectors(
                vectors=[embedding.tolist()],
                metadata=[metadata],
                ids=[memory_item.id]
            )

            if not success:
                log.warn("⚠️ 向量存储失败，但记忆已添加到图数据库")

            # 5. 添加实体信息到元数据
            memory_item.metadata["entities"] = [e.entity_id for e in entities]
            memory_item.metadata["relations"] = [
                f"{r.from_entity}-{r.relation_type}-{r.to_entity}" for r in relations
            ]

            # 6. 存储记忆
            self.semantic_memories.append(memory_item)

            log.success(f"✅ 添加语义记忆: {len(entities)}个实体, {len(relations)}个关系")
            return memory_item.id

        except Exception as e:
            log.error(f"❌ 添加语义记忆失败: {e}")
            raise

    def retrieve(self, query: str, limit: int = 5, **kwargs) -> List[MemoryItem]:
        """检索语义记忆"""
        try:
            user_id = kwargs.get("user_id")

            # 1. 向量检索
            vector_results = self._vector_search(query, limit * 2, user_id)

            # 2. 图检索
            graph_results = self._graph_search(query, limit * 2, user_id)

            # 3. 混合排序
            combined_results = self._combine_and_rank_results(
                vector_results, graph_results, query, limit
            )

            # 3.1 计算概率（对 combined_score 做 softmax 归一化）
            scores = [r.get("combined_score", r.get("vector_score", 0.0)) for r in combined_results]
            if scores:
                import math
                max_s = max(scores)
                exps = [math.exp(s - max_s) for s in scores]
                denom = sum(exps) or 1.0
                probs = [e / denom for e in exps]
            else:
                probs = []

            # 4. 过滤已遗忘记忆并转换为MemoryItem
            result_memories = []
            for idx, result in enumerate(combined_results):
                memory_id = result.get("memory_id")

                # 检查是否已遗忘
                memory = next((m for m in self.semantic_memories if m.id == memory_id), None)
                if memory and memory.metadata.get("forgotten", False):
                    continue  # 跳过已遗忘的记忆

                # 处理时间戳
                timestamp = result.get("timestamp")
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp)
                    except ValueError:
                        timestamp = datetime.now()
                elif isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp)
                else:
                    timestamp = datetime.now()

                # 直接从结果数据构建MemoryItem（附带分数与概率）
                memory_item = MemoryItem(
                    id=result["memory_id"],
                    content=result["content"],
                    memory_type="semantic",
                    user_id=result.get("user_id", "default"),
                    timestamp=timestamp,
                    importance=result.get("importance", 0.5),
                    metadata={
                        **result.get("metadata", {}),
                        "combined_score": result.get("combined_score", 0.0),
                        "vector_score": result.get("vector_score", 0.0),
                        "graph_score": result.get("graph_score", 0.0),
                        "probability": probs[idx] if idx < len(probs) else 0.0,
                    }
                )
                result_memories.append(memory_item)

            log.success(f"✅ 检索到 {len(result_memories)} 条相关记忆")
            return result_memories[:limit]

        except Exception as e:
            log.error(f"❌ 检索语义记忆失败: {e}")
            return []

    def _vector_search(self, query: str, limit: int, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Qdrant向量搜索"""
        try:
            # 生成查询向量
            query_embedding = self.embedding_model.encode(query)

            # 构建过滤条件
            where_filter = {"memory_type": "semantic"}
            if user_id:
                where_filter["user_id"] = user_id

            # Qdrant向量检索
            results = self.vector_store.search_similar(
                query_vector=query_embedding.tolist(),
                limit=limit,
                where=where_filter if where_filter else None
            )

            # 转换结果格式以保持兼容性
            formatted_results = []
            for result in results:
                formatted_result = {
                    "id": result["id"],
                    "score": result["score"],
                    **result["metadata"]  # 包含所有元数据
                }
                formatted_results.append(formatted_result)

            log.debug(f"🔍 Qdrant向量搜索返回 {len(formatted_results)} 个结果")
            return formatted_results

        except Exception as e:
            log.error(f"❌ Qdrant向量搜索失败: {e}")
            return []

    def _graph_search(self, query: str, limit: int, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Neo4j图搜索"""
        try:
            # 从查询中提取实体
            query_entities = self._extract_entities(query)

            if not query_entities:
                # 如果没有提取到实体，尝试按名称搜索
                entities_by_name = self.graph_store.search_entities_by_name(
                    name_pattern=query,
                    limit=10
                )
                if entities_by_name:
                    query_entities = [Entity(
                        entity_id=e["id"],
                        name=e["name"],
                        entity_type=e["type"]
                    ) for e in entities_by_name[:3]]
                else:
                    return []

            # 在Neo4j图中查找相关实体和记忆
            related_memory_ids = set()

            for entity in query_entities:
                try:
                    # 查找相关实体
                    related_entities = self.graph_store.find_related_entities(
                        entity_id=entity.entity_id,
                        max_depth=2,
                        limit=20
                    )

                    # 收集相关记忆ID
                    for rel_entity in related_entities:
                        if "memory_id" in rel_entity:
                            related_memory_ids.add(rel_entity["memory_id"])

                    # 也添加直接匹配的实体记忆
                    entity_rels = self.graph_store.get_entity_relationships(entity.entity_id)
                    for rel in entity_rels:
                        rel_data = rel.get("relationship", {})
                        if "memory_id" in rel_data:
                            related_memory_ids.add(rel_data["memory_id"])

                except Exception as e:
                    log.debug(f"图搜索实体 {entity.entity_id} 失败: {e}")
                    continue

            # 构建结果 - 从向量数据库获取完整记忆信息
            results = []
            for memory_id in list(related_memory_ids)[:limit * 2]:  # 获取更多候选
                try:
                    # 优先从本地缓存获取记忆详情，避免占位向量维度不一致问题
                    mem = self._find_memory_by_id(memory_id)
                    if not mem:
                        continue

                    if user_id and mem.user_id != user_id:
                        continue

                    metadata = {
                        "content": mem.content,
                        "user_id": mem.user_id,
                        "memory_type": mem.memory_type,
                        "importance": mem.importance,
                        "timestamp": int(mem.timestamp.timestamp()),
                        "entities": mem.metadata.get("entities", [])
                    }

                    # 计算图相关性分数
                    graph_score = self._calculate_graph_relevance_neo4j(metadata, query_entities)

                    results.append({
                        "id": memory_id,
                        "memory_id": memory_id,
                        "content": metadata.get("content", ""),
                        "similarity": graph_score,
                        "user_id": metadata.get("user_id"),
                        "memory_type": metadata.get("memory_type"),
                        "importance": metadata.get("importance", 0.5),
                        "timestamp": metadata.get("timestamp"),
                        "entities": metadata.get("entities", [])
                    })

                except Exception as e:
                    log.debug(f"获取记忆 {memory_id} 详情失败: {e}")
                    continue

            # 按图相关性排序
            results.sort(key=lambda x: x["similarity"], reverse=True)
            log.debug(f"🕸️ Neo4j图搜索返回 {len(results)} 个结果")
            return results[:limit]

        except Exception as e:
            log.error(f"❌ Neo4j图搜索失败: {e}")
            return []

    def _combine_and_rank_results(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """混合排序结果 - 仅基于向量与图分数的简单融合"""
        # 合并结果，按内容去重
        combined = {}
        content_seen = set()  # 用于内容去重

        # 添加向量结果
        for result in vector_results:
            memory_id = result["memory_id"]
            content = result.get("content", "")

            # 内容去重：检查是否已经有相同或高度相似的内容
            content_hash = hash(content.strip())
            if content_hash in content_seen:
                log.debug(f"⚠️ 跳过重复内容: {content[:30]}...")
                continue

            content_seen.add(content_hash)
            combined[memory_id] = {
                **result,
                "vector_score": result.get("score", 0.0),
                "graph_score": 0.0,
                "content_hash": content_hash
            }

        # 添加图结果
        for result in graph_results:
            memory_id = result["memory_id"]
            content = result.get("content", "")
            content_hash = hash(content.strip())

            if memory_id in combined:
                combined[memory_id]["graph_score"] = result.get("similarity", 0.0)
            elif content_hash not in content_seen:
                content_seen.add(content_hash)
                combined[memory_id] = {
                    **result,
                    "vector_score": 0.0,
                    "graph_score": result.get("similarity", 0.0),
                    "content_hash": content_hash
                }

        # 计算混合分数：相似度为主，重要性为辅助排序因子
        for memory_id, result in combined.items():
            vector_score = result["vector_score"]
            graph_score = result["graph_score"]
            importance = result.get("importance", 0.5)

            # 新评分算法：向量检索纯基于相似度，重要性作为加权因子
            # 基础相似度得分（不受重要性影响）
            base_relevance = vector_score * 0.7 + graph_score * 0.3

            # 重要性作为乘法加权因子，范围 [0.8, 1.2]
            # importance in [0,1] -> weight in [0.8,1.2]
            importance_weight = 0.8 + (importance * 0.4)

            # 最终得分：相似度 * 重要性权重
            combined_score = base_relevance * importance_weight

            # 调试信息：查看分数分解
            result["debug_info"] = {
                "base_relevance": base_relevance,
                "importance_weight": importance_weight,
                "combined_score": combined_score
            }

            result["combined_score"] = combined_score

        # 应用最小相关性阈值
        min_threshold = 0.1  # 最小相关性阈值
        filtered_results = [
            result for result in combined.values()
            if result["combined_score"] >= min_threshold
        ]

        # 排序并返回
        sorted_results = sorted(
            filtered_results,
            key=lambda x: x["combined_score"],
            reverse=True
        )

        # 调试信息
        log.debug(f"🔍 向量结果: {len(vector_results)}, 图结果: {len(graph_results)}")
        log.debug(f"📝 去重后: {len(combined)}, 过滤后: {len(filtered_results)}")

        for i, result in enumerate(sorted_results[:3]):
            log.debug(f"  结果{i + 1}: 向量={result['vector_score']:.3f}, 图={result['graph_score']:.3f}, 精确={result.get('exact_match_bonus', 0):.3f}, 关键词={result.get('keyword_bonus', 0):.3f}, 公司={result.get('company_bonus', 0):.3f}, 实体={result.get('entity_type_bonus', 0):.3f}, 综合={result['combined_score']:.3f}")

        return sorted_results[:limit]

    def _detect_language(self, text: str) -> str:
        """简单的语言检测"""
        # 统计中文字符比例（无正则，逐字符判断范围）
        chinese_chars = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
        total_chars = len(text.replace(' ', ''))

        if total_chars == 0:
            return "en"

        chinese_ratio = chinese_chars / total_chars
        return "zh" if chinese_ratio > 0.3 else "en"

    def _extract_entities(self, text: str) -> List[Entity]:
        """智能多语言实体提取"""
        entities = []

        # 检测文本语言
        lang = self._detect_language(text)

        # 选择合适的spaCy模型
        selected_nlp = None
        if lang == "zh" and "zh_core_web_sm" in self.nlp_models:
            selected_nlp = self.nlp_models["zh_core_web_sm"]
        elif lang == "en" and "en_core_web_sm" in self.nlp_models:
            selected_nlp = self.nlp_models["en_core_web_sm"]
        else:
            # 使用默认模型
            selected_nlp = self.nlp

        log.debug(f"🌐 检测语言: {lang}, 使用模型: {selected_nlp.meta['name'] if selected_nlp else 'None'}")

        # 使用spaCy进行实体识别和词法分析
        if selected_nlp:
            try:
                doc = selected_nlp(text)
                log.debug(f"📝 spaCy处理文本: '{text}' -> {len(doc.ents)} 个实体")

                # 存储词法分析结果，供Neo4j使用
                self._store_linguistic_analysis(doc, text)

                if not doc.ents:
                    # 如果没有实体，记录详细的词元信息
                    log.debug("🔍 未找到实体，词元分析:")
                    for token in doc[:5]:  # 只显示前5个词元
                        log.debug(f"   '{token.text}' -> POS: {token.pos_}, TAG: {token.tag_}, ENT_IOB: {token.ent_iob_}")

                for ent in doc.ents:
                    entity = Entity(
                        entity_id=f"entity_{hash(ent.text)}",
                        name=ent.text,
                        entity_type=ent.label_,
                        description=f"从文本中识别的{ent.label_}实体"
                    )
                    entities.append(entity)
                    # 安全获取置信度信息
                    confidence = "N/A"
                    try:
                        if hasattr(ent._, 'confidence'):
                            confidence = getattr(ent._, 'confidence', 'N/A')
                    except:
                        confidence = "N/A"

                    log.debug(f"🏷️ spaCy识别实体: '{ent.text}' -> {ent.label_} (置信度: {confidence})")

            except Exception as e:
                log.warn(f"⚠️ spaCy实体识别失败: {e}")
                import traceback
                log.debug(f"详细错误: {traceback.format_exc()}")
        else:
            log.warn("⚠️ 没有可用的spaCy模型进行实体识别")

        return entities

    