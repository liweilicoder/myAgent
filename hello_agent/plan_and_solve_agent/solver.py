from hello_agent.llm_client.llm_client import HelloAgentsLLM
from hello_agent.prompt.solver import SOLVER_PROMPT_TEMPLATE
import hello_agent.logger.logger as log

class Solver:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        history = ""
        final_answer = ""

        log.info("正在执行计划...")
        for i, step in enumerate(plan, 1):
            log.info(f"正在执行步骤 {i}/{len(plan)}: {step}")
            prompt = SOLVER_PROMPT_TEMPLATE.format(
                question=question, plan=plan, history=history if history else "无", current_step=step
            )
            messages = [{"role": "user", "content": prompt}]

            response_text = self.llm_client.think(messages=messages) or ""

            history += f"步骤 {i}: {step}\n结果: {response_text}\n\n"
            final_answer = response_text
            log.success(f"步骤 {i} 已完成，结果: {final_answer}")

        return final_answer
