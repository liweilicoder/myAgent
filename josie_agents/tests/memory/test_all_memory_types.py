import time
from datetime import datetime, timedelta

import josie_agents.utils.log as log
from josie_agents.tools.builtin.memory_tool import MemoryTool


class MemoryTypesDeepDive:
    """四种记忆类型深度解析演示类"""

    def __init__(self):
        self.setup_memory_systems()

    def setup_memory_systems(self):
        """设置不同的记忆系统"""
        log.delimiter("🧠 四种记忆类型深度解析")
        log.delimiter("=" * 60)

        # 创建专门的记忆工具实例
        self.working_memory_tool = MemoryTool(
            user_id="working_memory_user",
            memory_types=["working"]
        )

        self.episodic_memory_tool = MemoryTool(
            user_id="episodic_memory_user",
            memory_types=["episodic"]
        )

        self.semantic_memory_tool = MemoryTool(
            user_id="semantic_memory_user",
            memory_types=["semantic"]
        )

        self.perceptual_memory_tool = MemoryTool(
            user_id="perceptual_memory_user",
            memory_types=["perceptual"]
        )

        log.test("✅ 四种记忆系统初始化完成")

    def test_working_memory(self):
        """演示工作记忆的特点"""
        log.delimiter(" 💭 工作记忆 (Working Memory) 深度解析")
        log.delimiter("-" * 60)

        log.test("🔍 工作记忆特点:")
        log.test("• ⚡ 访问速度极快（纯内存存储）")
        log.test("• 📏 容量有限（默认50条记忆）")
        log.test("• ⏰ 自动过期（TTL机制）")
        log.test("• 🔄 适合临时信息存储")

        # 演示容量限制
        log.test(f" 1. 容量限制演示:")
        log.test("添加大量临时记忆，观察容量管理...")

        for i in range(8):
            content = f"临时工作记忆 {i + 1}: 当前正在处理任务步骤 {i + 1}"
            result = self.working_memory_tool.run({"action": "add",
                                                   "content": content,
                                                   "memory_type": "working",
                                                   "importance": 0.3 + (i * 0.1),
                                                   "task_step": i + 1})
            log.test(f"  添加记忆 {i + 1}: {result}")

        # 检查当前状态
        stats = self.working_memory_tool.run({"action": "stats"})
        log.test(f"当前工作记忆状态: {stats}")

        # 演示TTL机制
        log.test(f" 2. TTL（生存时间）机制演示:")

        # 添加一些带时间戳的记忆
        now = datetime.now()

        # 模拟不同时间的记忆
        time_memories = [
            ("刚刚的想法", now - timedelta(minutes=1), 1.5),
            ("20分钟前的任务", now - timedelta(minutes=20), 1.5),
            ("1小时前的提醒", now - timedelta(hours=1), 1.5),
            ("4h以前的笔记", now - timedelta(hours=4), 1.5)
        ]

        for content, ts, importance in time_memories:
            # 这里我们模拟时间差异
            result = self.working_memory_tool.run({"action": "add",
                                                   "content": content,
                                                   "memory_type": "working",
                                                   "importance": importance,
                                                   "timestamp": ts})
            log.test(f"  添加记忆: {content} ")

        # 演示快速检索
        log.test(f" 3. 快速检索演示:")

        search_queries = ["任务", "想法", "提醒"]

        for query in search_queries:
            start_time = time.time()
            results = self.working_memory_tool.run({"action": "search",
                                                    "query": query,
                                                    "memory_type": "working",
                                                    "limit": 3})
            search_time = time.time() - start_time
            log.test(f"查询 【{query}】: 耗时{search_time:.4f}秒")
            log.test(f"结果: {results[:500]}...")

        # 演示自动清理
        log.test(f" 4. 自动清理机制:")

        # 获取清理前的统计
        before_stats = self.working_memory_tool.run({"action": "stats"})
        log.test(f"清理前: {before_stats}")

        # 触发清理（通过遗忘低重要性记忆）
        forget_result = self.working_memory_tool.run({"action": "forget",
                                                      "strategy": "importance_based",
                                                      "threshold": 0.8})
        log.test(f"清理结果: {forget_result}")

        # 获取清理后的统计
        after_stats = self.working_memory_tool.run({"action": "stats"})
        log.test(f"清理后: {after_stats}")

    def test_episodic_memory(self):
        """演示情景记忆的特点"""
        log.delimiter("📖 情景记忆 (Episodic Memory) 深度解析")
        log.delimiter("-" * 60)

        log.test("🔍 情景记忆特点:")
        log.test("• 📅 完整的时间序列记录")
        log.test("• 🎭 丰富的上下文信息")
        log.test("• 🔗 支持记忆链条构建")
        log.test("• 💾 持久化存储")

        # 演示完整事件记录
        log.test(f" 1. 完整事件记录演示:")
        log.test("-" * 60)

        # 模拟一个完整的学习会话
        learning_session = [
            {
                "content": "开始学习Python机器学习",
                "context": "学习开始",
                "location": "家里书房",
                "mood": "专注",
                "importance": 0.7
            },
            {
                "content": "学习了线性回归的数学原理",
                "context": "理论学习",
                "chapter": "第3章",
                "difficulty": "中等",
                "importance": 0.8
            },
            {
                "content": "实现了第一个线性回归模型",
                "context": "实践编程",
                "code_lines": 45,
                "bugs_fixed": 2,
                "importance": 0.9
            },
            {
                "content": "完成了课后练习题",
                "context": "练习巩固",
                "exercises_completed": 5,
                "accuracy": 0.8,
                "importance": 0.6
            },
            {
                "content": "总结今天的学习收获",
                "context": "学习总结",
                "key_concepts": ["线性回归", "梯度下降", "损失函数"],
                "importance": 0.8
            }
        ]

        session_id = f"learning_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        for i, event in enumerate(learning_session):
            result = self.episodic_memory_tool.run({"action": "add",
                                                    "content": event["content"],
                                                    "memory_type": "episodic",
                                                    "importance": event["importance"],
                                                    "session_id": session_id,
                                                    "sequence_number": i + 1,
                                                    **{k: v for k, v in event.items() if
                                                       k not in ["content", "importance"]}})
            log.test(f"  事件 {i + 1}: {result}")

        # 演示时间序列检索
        log.test(f" 2. 时间序列检索演示:")
        log.test("-" * 60)

        # 按时间顺序检索
        timeline_search = self.episodic_memory_tool.run({"action": "search",
                                                         "query": "学习",
                                                         "memory_type": "episodic",
                                                         "session_id": "hahaha",
                                                         "limit": 10})
        log.test(f"学习时间线: {timeline_search}")

        # 按会话检索
        session_search = self.episodic_memory_tool.run({"action": "search",
                                                        "query": "线性回归",
                                                        "memory_type": "episodic",
                                                        "limit": 5})
        log.test(f"会话内容: {session_search}")

        # 演示上下文丰富性
        log.test(f" 3. 上下文信息演示:")
        log.test("-" * 60)

        # 添加带有丰富上下文的记忆
        rich_context_memory = {
            "content": "参加了AI技术分享会",
            "event_type": "conference",
            "location": "北京国际会议中心",
            "speakers": ["张教授", "李博士", "王工程师"],
            "topics": ["深度学习", "自然语言处理", "计算机视觉"],
            "attendees_count": 200,
            "duration_hours": 6,
            "weather": "晴朗",
            "transportation": "地铁",
            "networking_contacts": 3,
            "key_insights": ["Transformer架构的演进", "多模态学习的前景"],
            "follow_up_actions": ["阅读推荐论文", "尝试新框架"],
            "satisfaction_rating": 9
        }

        context_result = self.episodic_memory_tool.run({"action": "add",
                                                        "content": rich_context_memory["content"],
                                                        "memory_type": "episodic",
                                                        "importance": 0.9,
                                                        **{k: v for k, v in rich_context_memory.items() if
                                                           k != "content"}})
        log.test(f"丰富上下文记忆: {context_result}")

        # 演示记忆链条
        log.test(f"4. 记忆链条构建:")
        log.test("-" * 60)

        # 创建相关联的记忆序列
        memory_chain = [
            ("看到一篇关于GPT的论文", "trigger", None),
            ("决定深入研究Transformer架构", "decision", "trigger"),
            ("下载并阅读Attention is All You Need论文", "action", "decision"),
            ("实现了简化版的自注意力机制", "implementation", "action"),
            ("在项目中应用了学到的知识", "application", "implementation")
        ]

        chain_memories = {}
        for content, chain_type, parent_type in memory_chain:
            parent_id = chain_memories.get(parent_type) if parent_type else None

            result = self.episodic_memory_tool.run({"action": "add",
                                                    "content": content,
                                                    "memory_type": "episodic",
                                                    "importance": 0.7,
                                                    "chain_type": chain_type,
                                                    "parent_memory": parent_id,
                                                    "chain_id": "gpt_learning_chain"})

            # 提取记忆ID（简化处理）
            memory_id = f"{chain_type}_memory"
            chain_memories[chain_type] = memory_id
            log.test(f"  链条记忆: {content} (类型: {chain_type})")

        # 检索整个链条
        chain_search = self.episodic_memory_tool.run({"action": "search",
                                                      "query": "GPT Transformer",
                                                      "memory_type": "episodic",
                                                      "limit": 8})
        log.test(f"记忆链条检索: {chain_search}")

    def test_semantic_memory(self):
        """演示语义记忆的特点"""
        log.delimiter("🧠 语义记忆 (Semantic Memory) 深度解析")
        log.delimiter("-" * 60)

        log.test("🔍 语义记忆特点:")
        log.test("• 🔗 知识图谱结构化存储")
        log.test("• 🎯 概念和关系的抽象表示")
        log.test("• 🔍 语义相似度检索")
        log.test("• 🧮 支持推理和关联")

        # 演示概念存储
        log.test(f"1. 概念知识存储演示:")
        log.test("-" * 60)

        # 添加不同类型的概念知识
        concepts = [
            {
                "content": "机器学习是人工智能的一个分支，通过算法让计算机从数据中学习模式",
                "concept_type": "definition",
                "domain": "artificial_intelligence",
                "keywords": ["机器学习", "人工智能", "算法", "数据", "模式"],
                "importance": 0.9
            },
            {
                "content": "监督学习使用标记数据训练模型，包括分类和回归两大类任务",
                "concept_type": "category",
                "domain": "machine_learning",
                "parent_concept": "机器学习",
                "subcategories": ["分类", "回归"],
                "importance": 0.8
            },
            {
                "content": "梯度下降是一种优化算法，通过迭代更新参数来最小化损失函数",
                "concept_type": "algorithm",
                "domain": "optimization",
                "mathematical_basis": "微积分",
                "applications": ["神经网络训练", "线性回归"],
                "importance": 0.8
            },
            {
                "content": "过拟合是指模型在训练数据上表现很好，但在新数据上泛化能力差",
                "concept_type": "problem",
                "domain": "machine_learning",
                "causes": ["模型复杂度过高", "训练数据不足"],
                "solutions": ["正则化", "交叉验证", "早停"],
                "importance": 0.7
            }
        ]

        for concept in concepts:
            result = self.semantic_memory_tool.run({"action": "add",
                                                    "content": concept["content"],
                                                    "memory_type": "semantic",
                                                    "importance": concept["importance"],
                                                    **{k: v for k, v in concept.items() if
                                                       k not in ["content", "importance"]}})
            log.test(f"  概念存储: {concept['concept_type']} - {result}")

        # 演示关系推理
        log.test(f" 2. 关系推理演示:")
        log.test("-" * 60)

        # 添加关系知识
        relationships = [
            {
                "content": "深度学习是机器学习的子集，使用多层神经网络",
                "relation_type": "is_subset_of",
                "subject": "深度学习",
                "object": "机器学习",
                "strength": 0.9
            },
            {
                "content": "卷积神经网络特别适合处理图像数据",
                "relation_type": "suitable_for",
                "subject": "卷积神经网络",
                "object": "图像处理",
                "strength": 0.8
            },
            {
                "content": "反向传播算法用于训练神经网络",
                "relation_type": "used_for",
                "subject": "反向传播",
                "object": "神经网络训练",
                "strength": 0.9
            }
        ]

        for relation in relationships:
            result = self.semantic_memory_tool.run({"action": "add",
                                                    "content": relation["content"],
                                                    "memory_type": "semantic",
                                                    "importance": 0.8,
                                                    **{k: v for k, v in relation.items() if k != "content"}})
            log.test(f"  关系存储: {relation['relation_type']} - {result}")

        # 演示语义检索
        log.test(f"3. 语义相似度检索:")
        log.test("-" * 60)

        semantic_queries = [
            "什么是人工智能？",
            "如何防止模型过拟合？",
            "神经网络的训练方法",
            "图像识别技术"
        ]

        for query in semantic_queries:
            start_time = time.time()
            results = self.semantic_memory_tool.run({"action": "search",
                                                     "query": query,
                                                     "memory_type": "semantic",
                                                     "limit": 3})
            search_time = time.time() - start_time
            log.test(f"查询: '{query}' ({search_time:.4f}秒)")
            log.test(f"结果: {results[:150]}...")

        # 演示知识图谱构建
        log.test(f" 4. 知识图谱构建:")
        log.test("-" * 60)

        # 添加实体和关系
        entities_and_relations = [
            {
                "content": "TensorFlow是Google开发的深度学习框架",
                "entity_type": "framework",
                "developer": "Google",
                "domain": "deep_learning",
                "language": "Python",
                "year": 2015
            },
            {
                "content": "PyTorch是Facebook开发的深度学习框架，以动态图著称",
                "entity_type": "framework",
                "developer": "Facebook",
                "domain": "deep_learning",
                "feature": "dynamic_graph",
                "language": "Python"
            },
            {
                "content": "BERT是基于Transformer的预训练语言模型",
                "entity_type": "model",
                "architecture": "Transformer",
                "task": "natural_language_processing",
                "training_method": "pre_training"
            }
        ]

        for item in entities_and_relations:
            result = self.semantic_memory_tool.run({"action": "add",
                                                    "content": item["content"],
                                                    "memory_type": "semantic",
                                                    "importance": 0.8,
                                                    **{k: v for k, v in item.items() if k != "content"}})
            log.test(f"实体关系: {item['entity_type']} - {result}")

        # 获取语义记忆统计
        semantic_stats = self.semantic_memory_tool.run({"action": "stats"})
        log.test(f"语义记忆统计: {semantic_stats}")

    def test_perceptual_memory(self):
        """演示感知记忆的特点"""
        log.delimiter("👁️ 感知记忆 (Perceptual Memory) 深度解析")
        log.delimiter("-" * 60)

        log.test("🔍 感知记忆特点:")
        log.test("• 🎨 多模态数据支持")
        log.test("• 🔄 跨模态相似性搜索")
        log.test("• 📊 感知数据的语义理解")
        log.test("• 🎯 内容生成和检索")

        # 演示文本感知记忆
        log.test(f"1. 文本感知记忆:")
        log.test("-" * 60)

        text_perceptions = [
            {
                "content": "这是一段优美的诗歌：春江潮水连海平，海上明月共潮生",
                "modality": "text",
                "genre": "poetry",
                "emotion": "peaceful",
                "language": "chinese",
                "aesthetic_value": 0.9
            },
            {
                "content": "技术文档：API接口返回JSON格式数据，包含状态码和响应体",
                "modality": "text",
                "genre": "technical",
                "complexity": "medium",
                "language": "chinese",
                "practical_value": 0.8
            }
        ]

        for perception in text_perceptions:
            result = self.perceptual_memory_tool.run({"action": "add",
                                                      "content": perception["content"],
                                                      "memory_type": "perceptual",
                                                      "importance": 0.7,
                                                      **{k: v for k, v in perception.items() if k != "content"}})
            log.test(f"  文本感知: {perception['genre']} - {result}")

        # 演示图像感知记忆（模拟）
        log.test(f" 2. 图像感知记忆（模拟）:")
        log.test("-" * 60)

        # 模拟图像数据
        image_perceptions = [
            {
                "content": "一张美丽的日落风景照片",
                "modality": "image",
                "file_path": "/Users/jesse/PythonProjects/myAgent/josie_agents/tests/memory/simulated/sunset.jpg",
                "scene_type": "landscape",
                "colors": ["orange", "red", "purple"],
                "objects": ["sun", "clouds", "horizon"],
                "mood": "serene",
                "quality": "high"
            },
            {
                "content": "技术架构图展示了微服务系统设计",
                "modality": "image",
                "file_path": "/Users/jesse/PythonProjects/myAgent/josie_agents/tests/memory/simulated/architecture.png",
                "diagram_type": "technical",
                "components": ["API Gateway", "Services", "Database"],
                "complexity": "high",
                "purpose": "documentation"
            }
        ]

        for perception in image_perceptions:
            result = self.perceptual_memory_tool.run({"action": "add",
                                                      "content": perception["content"],
                                                      "memory_type": "perceptual",
                                                      "importance": 0.8,
                                                      **{k: v for k, v in perception.items() if k != "content"}})
            log.test(f"  图像感知: {perception['content']} - {result}")

        # 演示音频感知记忆（模拟）
        log.test(f" 3. 音频感知记忆（模拟）:")
        log.test("-" * 60)

        audio_perceptions = [
            {
                "content": "一段优美的古典音乐演奏",
                "modality": "audio",
                "file_path": "/Users/jesse/PythonProjects/myAgent/josie_agents/tests/memory/simulated/classical.mp3",
                "genre": "classical",
                "instruments": ["piano", "violin", "cello"],
                "tempo": "andante",
                "emotion": "elegant",
                "duration_seconds": 240
            },
        ]

        for perception in audio_perceptions:
            result = self.perceptual_memory_tool.run({"action": "add",
                                                      "content": perception["content"],
                                                      "memory_type": "perceptual",
                                                      "importance": 0.7,
                                                      **{k: v for k, v in perception.items() if k != "content"}})
            log.test(f"  音频感知: {perception['content']} - {result}")

        # 演示跨模态检索
        log.test(f"4. 跨模态检索演示:")
        log.test("-" * 60)

        cross_modal_queries = [
            ("美丽的风景", "寻找视觉美感相关内容", "image"),
            ("技术文档", "查找技术相关的多模态内容","text"),
            ("音乐和艺术", "检索艺术相关的感知记忆","audio")
        ]

        for query, description, mod in cross_modal_queries:
            results = self.perceptual_memory_tool.run({"action": "search",
                                                       "query": query,
                                                       "memory_type": "perceptual",
                                                       "limit": 3,
                                                       "target_modality": mod
                                                       })
            log.test(f"  跨模态查询: '{query}' ({description})({mod})")
            log.test(f"    结果: {results[:120]}...")

        # 演示感知特征分析
        log.test(f"5. 感知特征分析:")
        log.test("-" * 60)

        # 获取感知记忆统计
        perceptual_stats = self.perceptual_memory_tool.run({"action": "stats"})
        log.test(f"感知记忆统计: {perceptual_stats}")

        # 分析不同模态的分布
        modality_analysis = self.perceptual_memory_tool.run({"action": "search",
                                                             "query": "模态分析",
                                                             "memory_type": "perceptual",
                                                             "limit": 10})
        log.test(f"模态分布分析: {modality_analysis}")

    def cleanup(self):
        log.delimiter("清空全部记忆，清理测试环境")
        result = self.working_memory_tool.run({
            "action": "clear_all",
        })
        log.test(f"WorkingMemory:{result}")

        result = self.episodic_memory_tool.run({
            "action": "clear_all",
        })
        log.test(f"EpisodicMemory:{result}")

        result = self.semantic_memory_tool.run({
            "action": "clear_all",
        })
        log.test(f"SemanticMemory:{result}")

        result = self.perceptual_memory_tool.run({
            "action": "clear_all",
        })
        log.test(f"PerceptualMemory:{result}")


def main():
    demo = MemoryTypesDeepDive()

    # 前置清理环境
    demo.cleanup()

    #demo.test_working_memory()

    #demo.test_episodic_memory()

    #demo.test_semantic_memory()

    demo.test_perceptual_memory()

    # 后置清理环境
    #demo.cleanup()

if __name__ == "__main__":
    main()
