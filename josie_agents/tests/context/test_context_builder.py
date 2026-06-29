"""
ContextBuilder 与 Agent 集成示例

展示如何将 ContextBuilder 集成到 Agent 中，实现：
1. 上下文感知的 Agent
2. 自动构建优化的上下文
3. 记忆管理与上下文构建的协同
"""
from datetime import datetime

from josie_agents.agents.josie_simple_agent import JosieSimpleAgent
from josie_agents.context.builder import ContextBuilder, ContextConfig
from josie_agents.core.josie_llm import JosieLLM
from josie_agents.core.message import Message

import josie_agents.utils.log as log
from josie_agents.utils.trim import clean_llm_resp

class ContextAwareAgent(JosieSimpleAgent):
    """具有上下文感知能力的 Agent"""

    def __init__(self, name: str, llm: JosieLLM, **kwargs):
        super().__init__(name=name, llm=llm, **kwargs)


        #（Optional）
        # self.memory_tool = MemoryTool(user_id=kwargs.get("user_id", "default"))
        # self.rag_tool = RAGTool(knowledge_base_path=kwargs.get("knowledge_base_path", "./kb"))

        # 初始化上下文构建器
        self.context_builder = ContextBuilder(
            # memory_tool=self.memory_tool,
            # rag_tool=self.rag_tool,
            config=ContextConfig(max_tokens=4000)
        )

        self.conversation_history = []

    def run(self, user_input: str) -> str:
        """运行 Agent,自动构建优化的上下文"""

        # 1. 使用 ContextBuilder 构建优化的上下文
        optimized_context = self.context_builder.build(
            user_query=user_input,
            conversation_history=self.conversation_history,
            system_instructions=self.system_prompt
        )

        # 2. 使用优化后的上下文调用 LLM
        messages = [
            {"role": "system", "content": optimized_context},
            {"role": "user", "content": user_input}
        ]
        response = self.llm.invoke(messages)
        response = clean_llm_resp(response)

        # 3. 更新对话历史
        self.conversation_history.append(
            Message(content=user_input, role="user", timestamp=datetime.now())
        )
        self.conversation_history.append(
            Message(content=response, role="assistant", timestamp=datetime.now())
        )

        # 4. 将重要交互记录到记忆系统
        # self.memory_tool.run({
        #     "action": "add",
        #     "content": f"Q: {user_input}\nA: {response[:200]}...",  # 摘要
        #     "memory_type": "episodic",
        #     "importance": 0.6
        # })

        return response


def main():
    log.delimiter("=" * 80)
    log.delimiter("ContextBuilder 与 Agent 集成示例")
    log.delimiter("=" * 80 )

    # 配置 LLM
    llm = JosieLLM()

    # 使用示例
    agent = ContextAwareAgent(
        name="数据分析顾问",
        llm=llm,
        system_prompt="你是一位资深的Python数据工程顾问。"
    )

    # 进行对话
    response = agent.run("如何优化Pandas的内存占用?")
    log.test(f"助手回答:\n{response}\n")

    # 继续对话
    response = agent.run("能给出优化Pandas的内存占用代码示例吗?")
    log.test(f"助手回答:\n{response}\n")

    log.test("=" * 80)


if __name__ == "__main__":
    main()
