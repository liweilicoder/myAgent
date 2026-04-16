import re
import os
from dotenv import load_dotenv
from agent.llm.llm import OpenAIClient
from agent.simple_agent.prompt import AGENT_SYSTEM_PROMPT
from agent.simple_agent.available_tools import available_tools
import agent.logger as log

load_dotenv('/Users/jesse/PythonProjects/myAgent/.env', override=True)

API_KEY = os.getenv('MINIMAX_API_KEY')
BASE_URL = os.getenv('MINIMAX_BASE_URL')
MODEL = os.getenv('MINIMAX_MODEL')

llm = OpenAIClient(
    model=MODEL,
    api_key=API_KEY,
    base_url=BASE_URL
)

def chat(user_prompt: str):
    prompt_history = [f"用户请求: {user_prompt}"]

    log.info(f"用户输入: {user_prompt}")
    log.separator()

    for i in range(8):
        log.debug(f"循环 {i + 1}")

        full_prompt = "\n".join(prompt_history)

        llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)

        indented_prompt = "\n".join(f"  {line}" for line in full_prompt.split("\n"))
        log.debug(f"llm模型输入:\n{indented_prompt}\n")

        match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
                log.debug("已截断多余的 Thought-Action 对")


        indented_output = "\n".join(f"  {line}" for line in llm_output.split("\n"))
        log.debug(f"模型输出:\n{indented_output}\n")

        prompt_history.append(llm_output)

        action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
        if not action_match:
            observation = "错误: 未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
            observation_str = f"Observation: {observation}"
            log.warn(observation_str)
            log.separator()
            prompt_history.append(observation_str)
            continue
        action_str = action_match.group(1).strip()

        if action_str.startswith("Finish"):
            match = re.match(r"Finish\[(.*)\]", action_str)
            if match:
                final_answer = match.group(1)
                log.success(f"任务完成，最终答案: {final_answer}")
                break
            else:
                observation = "错误：Finish 格式不正确，应为 Finish[答案]"
                observation_str = f"Observation: {observation}"
                log.warn(observation_str)
                log.separator()
                prompt_history.append(observation_str)
                continue

        tool_name = re.search(r"(\w+)\(", action_str).group(1)
        args_str = re.search(r"\((.*)\)", action_str).group(1)
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

        if tool_name in available_tools:
            log.info(f"调用工具: {tool_name}")
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f"错误：未定义的工具 '{tool_name}'"
            log.error(observation)

        observation_str = f"Observation: {observation}"
        log.info(observation_str)
        log.separator()
        prompt_history.append(observation_str)
