JOSIE_REACT_PROMPT = """你是一个具备推理和行动能力的AI助手。你可以通过思考分析问题，然后调用合适的工具来获取信息，最终给出准确的答案。

## 可用工具
{tools}

## 工作流程
请严格按照以下格式进行回应，每次只能执行一个步骤：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]` - 调用指定工具
- `Finish[最终答案]` - 当你有足够信息给出最终答案时

## 重要提醒
1. 每次回应必须包含Thought和Action两部分
2. 工具调用的格式必须严格遵循：工具名[参数]
3. 只有当你确信有足够信息回答问题时，才使用Finish
4. 如果工具返回的信息不够，继续使用其他工具或相同工具的不同参数

示例:
    Thought: 用户问的是苹果手机最新型号，这是一个关于时事的问题，我需要搜索来获取最新信息。
    Action: Search[苹果手机最新型号是什么？]

    (工具返回观察后，继续推理...)
    Thought: 通过搜索我得知苹果最新型号是 iPhone 16 Pro Max，我需要获取更多关于其卖点的信息。
    Action: Search[iPhone 16 Pro Max 卖点]

    (收集到足够信息后...)
    Thought: 根据搜索结果，我已经获得了苹果最新型号及其卖点的完整信息，可以给出最终答案了。
    Action: Finish[苹果最新型号是 iPhone 16 Pro Max，卖点包括 A18 Pro 芯片、钛金属边框、5倍光学变焦等。]

## 当前任务
**Question:** {question}

## 执行历史
{history}

现在开始你的推理和行动：
"""

import re
import josie_agents.utils.log as log
from typing import Optional, List
from josie_agents.core.josie_llm import JosieLLM
from josie_agents.agents.base_agent import BaseAgent
from josie_agents.core.config import Config
from josie_agents.core.message import Message
from josie_agents.tools.registry import ToolRegistry


class JosieReactAgent(BaseAgent):
    """
    JosieReactAgent- 推理与行动结合的智能体
    """
    def __init__(
        self,
        name: str,
        llm: JosieLLM,
        tool_registry: ToolRegistry,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 5,
        custom_prompt: Optional[str] = None
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.current_history: List[str] = []
        self.prompt_template = custom_prompt if custom_prompt else JOSIE_REACT_PROMPT
        log.success(f"✅ {name} 初始化完成，最大步数: {max_steps}")

    def run(self, input_text: str, **kwargs) -> str:
        """运行ReAct Agent"""
        self.current_history = []
        current_step = 0
        log.info(f"🤖 {self.name} 开始处理问题: {input_text}")

        while current_step < self.max_steps:
            current_step += 1
            log.delimiter(f"--- 第 {current_step} 步 ---")

            # 1. 构建提示词
            tools_desc = self.tool_registry.get_tools_description()

            history_parts = []
            for i in range(0, len(self.current_history), 2):
                step = i // 2 + 1
                history_parts.append(f"【Step {step}】 {self.current_history[i]}")
                if i + 1 < len(self.current_history):
                    history_parts.append(f"【Step {step}】 {self.current_history[i + 1]}")
                if i + 2 < len(self.current_history):
                    history_parts.append("---------------------------------------")
            history_str = "\n".join(history_parts)

            prompt = self.prompt_template.format(
                tools=tools_desc,
                question=input_text,
                history=history_str
            )

            # 2. 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm.invoke(messages, **kwargs)

            # 3. 解析输出
            thought, action = self._parse_output(response_text)

            # 4. 检查完成条件
            if action and action.startswith("Finish"):
                # 如果是Finish指令，提取最终答案并结束
                final_answer = self._parse_action_input(action)
                log.success(f"🎉 最终答案: {final_answer}")
                self.add_message(Message(input_text, "user"))
                self.add_message(Message(final_answer, "assistant"))
                return final_answer

            # 5. 执行工具调用
            if action:
                tool_name, tool_input = self._parse_action(action)
                log.info(f"🎬 行动: {tool_name}[{tool_input}]")
                observation = self.tool_registry.execute_tool(tool_name, tool_input)
                log.info(f"👀 观察: {observation}")
                self.current_history.append(f"Action: {action}")
                self.current_history.append(f"Observation: {observation}")

        # 达到最大步数
        final_answer = "抱歉，我无法在限定步数内完成这个任务。"
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        return final_answer

    def _parse_output(self, text: str):
        # 跨行正则移除所有 <think ...>...</think> 块；若出现未闭合 <think>，从 <think> 起丢弃到文本末尾，防止继续误解析
        text = re.sub(r"<think\b[^>]*>.*?</think\s*>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<think\b[^>]*>.*\Z", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Thought: 匹配到 Action: 或文本末尾
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: 匹配到文本末尾
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        return (match.group(1), match.group(2)) if match else (None, None)

    def _parse_action_input(self, action_text: str):
        match = re.match(r"\w+\[(.*)\]", action_text, re.DOTALL)
        return match.group(1) if match else ""
