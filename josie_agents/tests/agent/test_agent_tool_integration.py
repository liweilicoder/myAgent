"""
    在Agents框架中集成MemoryTool和RAGTool
"""
from dotenv import load_dotenv
import josie_agents.utils.log as log
from josie_agents.agents.josie_simple_agent import JosieSimpleAgent
from josie_agents.core.josie_llm import JosieLLM

from josie_agents.tools.builtin.memory_tool import MemoryTool
from josie_agents.tools.builtin.rag_tool import RAGTool
from josie_agents.tools.registry import ToolRegistry

load_dotenv()

class AgentIntegrationDemo:
    """Agent工具集成演示类"""

    def __init__(self):
        self.setup_agent()

    def setup_agent(self):
        """设置Agent和工具"""
        log.delimiter("🤖 Agent工具集成设置")
        log.delimiter("=" * 50)

        # 初始化工具
        log.test("1. 初始化工具...")
        self.memory_tool = MemoryTool(
            user_id="agent_integration_user",
            memory_types=["working", "episodic"]
        )

        self.rag_tool = RAGTool(
            knowledge_base_path="./agent_integration_kb",
            rag_namespace="agent_demo"
        )

        log.delimiter("✅ MemoryTool和RAGTool初始化完成")

        # 创建Agent
        log.test(" 2. 创建Agent...")
        self.llm = JosieLLM()
        self.agent = JosieSimpleAgent(
            name="智能学习助手",
            llm=self.llm,
            system_prompt="集成记忆和RAG功能的智能助手"
        )

        log.delimiter("✅ Agent创建完成")

        # 注册工具
        log.test(" 3. 注册工具...")
        self.tool_registry = ToolRegistry()
        self.tool_registry.register_tool(self.memory_tool)
        self.tool_registry.register_tool(self.rag_tool)
        self.agent.tool_registry = self.tool_registry

        log.delimiter("✅ 工具注册完成")

        # 显示Agent状态
        log.test(f" 📊 Agent状态:")
        log.test(f"  名称: {self.agent.name}")
        log.test(f"  描述: {self.agent.system_prompt}")
        log.test(f"  可用工具: {list(self.tool_registry._tools.keys())}")

    def test_tool_registry_pattern(self):
        """演示工具注册模式"""
        log.delimiter("🔧 工具注册模式演示")
        log.delimiter("-" * 50)

        log.test("工具注册模式特点:")
        log.test("• 🔌 统一的工具接口")
        log.test("• 📋 集中的工具管理")
        log.test("• 🔄 动态工具加载")
        log.test("• 🎯 工具能力发现")

        # 演示工具注册过程
        log.test(f"🔧工具注册详情:")
        log.test("--------")

        for tool_name, tool_instance in self.tool_registry._tools.items():
            log.test(f"\t工具: {tool_name}")
            log.test(f"\t类型: {type(tool_instance).__name__}")
            log.test(f"\t描述: {tool_instance.description}")

            # 显示工具的主要功能
            if tool_name == "memory":
                log.test(f"\t主要功能: 记忆管理、搜索、整合、遗忘")
                log.test(f"\t记忆类型: {tool_instance.memory_types}")
            elif tool_name == "rag":
                log.test(f"\t主要功能: 文档处理、智能问答、知识检索")
                log.test(f"\t命名空间: {tool_instance.rag_namespace}")

            log.test("--------")

        # 演示工具发现机制
        log.test(f" 🔍 工具能力发现:")
        available_tools = self.tool_registry.list_tools()
        log.test(f"可用工具列表: {available_tools}")

        # 演示工具获取
        memory_tool = self.tool_registry.get_tool("memory")
        rag_tool = self.tool_registry.get_tool("rag")

        log.test(f" ✅ 工具获取成功:")
        log.test(f"  Memory工具: {type(memory_tool).__name__}")
        log.test(f"  RAG工具: {type(rag_tool).__name__}")

    def test_unified_interface(self):
        """演示统一接口模式"""
        log.delimiter(" 🔗 统一接口模式演示")
        log.delimiter("-" * 50)

        log.test("统一接口优势:")
        log.test("• 🎯 一致的调用方式")
        log.test("• 📝 标准化的参数传递")
        log.test("• 🛡️ 统一的错误处理")
        log.test("• 🔄 简化的工具切换")

        # 演示统一的run接口
        log.test(f" 🔗 统一run接口演示:")

        # Memory工具操作
        log.test("-"*50)
        log.test(f" 1. Memory工具操作:")
        memory_operations = [
            ("add", {
                "content": "学习了Agent工具集成模式",
                "memory_type": "episodic",
                "importance": 0.8,
                "topic": "agent_integration"
            }),
            ("search", {
                "query": "Agent集成",
                "limit": 2
            }),
            ("stats", {})
        ]

        for operation, params in memory_operations:
            log.test(f"  操作: memory.run('{operation}', {params})")
            result = self.memory_tool.run({"action": operation, **params})
            log.test(f"  结果: {str(result)[:100]}...")

        # RAG工具操作
        log.test("-" * 50)
        log.test(f" 2. RAG工具操作:")

        # 先添加一些内容
        self.rag_tool.run({"action": "add_text",
                           "text": "Agent工具集成是HelloAgents框架的核心特性，允许Agent使用多种工具来完成复杂任务。",
                           "document_id": "agent_integration_guide"})

        rag_operations = [
            ("search", {
                "query": "Agent工具集成",
                "limit": 2
            }),
            ("ask", {
                "question": "什么是Agent工具集成？",
                "limit": 2
            }),
            ("stats", {})
        ]

        for operation, params in rag_operations:
            log.test(f"  操作: rag.run('{operation}', {params})")
            result = self.rag_tool.run({"action": operation, **params})
            log.test(f"  结果: {str(result)[:500]}...")

    def test_collaborative_workflow(self):
        """演示协同工作流程"""
        log.delimiter(" 🤝 协同工作流程演示")
        log.delimiter("-" * 50)

        log.test("协同工作场景:")
        log.test("• 📚 学习新知识 → RAG存储 + Memory记录")
        log.test("• 🔍 回顾学习历程 → Memory检索 + RAG补充")
        log.test("• 💡 知识应用 → RAG查询 + Memory更新")
        log.test("• 📊 学习分析 → 两工具统计整合")

        # 场景1：学习新知识
        log.test("-" * 50)
        log.test(f" 📚 场景1：学习新知识")

        # 向RAG添加学习资料
        learning_content = """# 设计模式：观察者模式

## 定义
观察者模式定义了对象间的一对多依赖关系，当一个对象的状态发生改变时，所有依赖它的对象都会得到通知并自动更新。

## 结构
- Subject（主题）：维护观察者列表，提供注册和删除观察者的方法
- Observer（观察者）：定义更新接口
- ConcreteSubject（具体主题）：实现主题接口
- ConcreteObserver（具体观察者）：实现观察者接口

## 应用场景
- GUI事件处理
- 模型-视图架构
- 发布-订阅系统
"""

        rag_result = self.rag_tool.run({"action": "add_text",
                                        "text": learning_content,
                                        "document_id": "observer_pattern"})
        log.test(f"RAG添加结果: {rag_result}")

        # 记录学习活动到记忆系统
        memory_result = self.memory_tool.run({"action": "add",
                                              "content": "学习了观察者设计模式的定义、结构和应用场景",
                                              "memory_type": "episodic",
                                              "importance": 0.8,
                                              "topic": "design_patterns",
                                              "pattern_type": "observer"})
        log.test(f"Memory记录结果: {memory_result}")

        # 场景2：回顾学习历程
        log.test("-" * 50)
        log.test(f" 🔍 场景2：回顾学习历程")

        # 从记忆系统检索学习历史
        memory_search = self.memory_tool.run({"action": "search",
                                              "query": "设计模式学习",
                                              "limit": 3})
        log.test(f"学习历史回顾: {memory_search}")

        # 从RAG获取相关知识补充
        rag_search = self.rag_tool.run({"action": "search",
                                        "query": "观察者模式",
                                        "limit": 2})
        log.test(f"知识内容补充: {rag_search}")

        # 场景3：知识应用
        log.test("-" * 50)
        log.test(f" 💡 场景3：知识应用")

        # 通过RAG查询应用方法
        application_query = self.rag_tool.run({"action": "ask",
                                               "question": "观察者模式适用于什么场景？",
                                               "limit": 2})
        log.test(f"应用场景查询: {application_query}")

        # 记录应用实践到记忆
        application_memory = self.memory_tool.run({"action": "add",
                                                   "content": "查询了观察者模式的应用场景，准备在GUI项目中使用",
                                                   "memory_type": "working",
                                                   "importance": 0.7,
                                                   "application_context": "gui_project"})
        log.test(f"应用记录: {application_memory}")

        # 场景4：学习分析
        log.test("-" * 50)
        log.test(f" 📊 场景4：学习分析")

        # 获取记忆系统统计
        memory_stats = self.memory_tool.run({"action": "stats"})
        log.test(f"记忆统计: {memory_stats}")

        # 获取RAG系统统计
        rag_stats = self.rag_tool.run({"action": "stats"})
        log.test(f"知识库统计: {rag_stats}")

        # 生成学习摘要
        learning_summary = self.memory_tool.run({"action": "summary", "limit": 5})
        log.test(f"学习摘要: {learning_summary}")

    def test_agent_orchestration(self):
        """演示Agent编排能力"""
        log.delimiter(" 🎭 Agent编排能力演示")
        log.delimiter("-" * 50)

        log.test("Agent编排特点:")
        log.test("• 🧠 智能工具选择")
        log.test("• 🔄 工具链式调用")
        log.test("• 📊 结果整合分析")
        log.test("• 🎯 目标导向执行")

        # 模拟复杂任务的工具编排
        log.test(f" 🎭 复杂任务编排示例:")
        log.test(f"任务: 创建一个关于机器学习的学习计划")

        # 步骤1：从RAG获取机器学习知识结构
        log.test(f" 步骤1: 获取知识结构")

        # 添加机器学习知识
        ml_content = """# 机器学习学习路径

## 基础阶段
1. 数学基础：线性代数、概率统计、微积分
2. 编程基础：Python、NumPy、Pandas
3. 机器学习概念：监督学习、无监督学习、强化学习

## 进阶阶段
1. 算法实现：从零实现经典算法
2. 深度学习：神经网络、CNN、RNN、Transformer
3. 实践项目：端到端机器学习项目

## 高级阶段
1. 模型优化：超参数调优、模型压缩
2. 部署运维：模型部署、监控、更新
3. 前沿技术：最新论文、开源项目
"""

        self.rag_tool.run({"action": "add_text",
                           "text": ml_content,
                           "document_id": "ml_learning_path"})

        knowledge_structure = self.rag_tool.run({"action": "ask",
                                                 "question": "机器学习的学习路径是什么？",
                                                 "limit": 3})
        log.test(f"知识结构: {knowledge_structure[:200]}...")

        # 步骤2：记录学习计划到记忆系统
        log.test(f" 步骤2: 记录学习计划")

        plan_memory = self.memory_tool.run({"action": "add",
                                            "content": "制定了机器学习学习计划，包括基础、进阶、高级三个阶段",
                                            "memory_type": "episodic",
                                            "importance": 0.9,
                                            "plan_type": "learning",
                                            "subject": "machine_learning"})
        log.test(f"计划记录: {plan_memory}")

        # 步骤3：检索相关学习经验
        log.test(f" 步骤3: 检索学习经验")

        experience_search = self.memory_tool.run({"action": "search",
                                                  "query": "学习计划 学习经验",
                                                  "limit": 3})
        log.test(f"相关经验: {experience_search}")

        # 步骤4：整合生成最终建议
        log.test(f" 步骤4: 生成最终建议")

        final_advice = self.rag_tool.run({"action": "ask",
                                          "question": "如何制定有效的机器学习学习计划？",
                                          "limit": 4})
        log.test(f"最终建议: {final_advice[:300]}...")

        # 记录编排过程
        orchestration_memory = self.memory_tool.run({"action": "add",
                                                     "content": "完成了复杂的学习计划制定任务，使用了RAG和Memory的协同编排",
                                                     "memory_type": "working",
                                                     "importance": 0.8,
                                                     "task_type": "orchestration"})
        log.test(f" 编排记录: {orchestration_memory}")

    def cleanup(self):
        log.delimiter("清理测试环境")
        result = self.memory_tool.run({
            "action": "clear_all",
        })
        log.test(f" 🧹 清空记忆{result}")

        ret = self.rag_tool._clear_knowledge_base(confirm=True)
        log.test(f" 🧹 清空知识库{ret}")

def main():
    """主函数"""
    log.delimiter("🤖 Agent工具集成演示")
    log.delimiter("展示如何在Agents框架中集成MemoryTool和RAGTool")
    log.delimiter("=" * 70)

    try:
        demo = AgentIntegrationDemo()

        # 1. 工具注册模式演示
        #demo.test_tool_registry_pattern()

        # 2. 统一接口模式演示
        #demo.test_unified_interface()

        # 3. 协同工作流程演示
        #demo.test_collaborative_workflow()

        # 4. Agent编排能力演示
        demo.test_agent_orchestration()

        demo.cleanup()


    except Exception as e:
        log.error(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()