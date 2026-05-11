from hello_agent.llm_client.llm_client import HelloAgentsLLM
from hello_agent.prompt.planner import PLANNER_PROMPT_TEMPLATE
import hello_agent.logger.logger as log
import ast

class Planner:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        messages = [{"role": "user", "content": prompt}]

        log.info("正在生成计划...")
        response_text = self.llm_client.think(messages=messages) or ""
        log.success(f"计划已生成:\n{response_text}")

        try:
            # 只提取第一个 python 代码块的内容
            parts = response_text.split("```python")
            if len(parts) < 2:
                raise ValueError("未找到 python 代码块")
            plan_str = parts[1].split("```")[0].strip()
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            log.error(f"解析计划时出错: {e}")
            log.debug(f"原始响应: {response_text}")
            return []
        except Exception as e:
            log.error(f"解析计划时发生未知错误: {e}")
            return []
