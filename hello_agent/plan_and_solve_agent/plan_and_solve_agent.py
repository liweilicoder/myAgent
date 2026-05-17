from hello_agent.llm_client.llm_client import HelloAgentsLLM
from hello_agent.plan_and_solve_agent.planner import Planner
from hello_agent.plan_and_solve_agent.solver import Solver
import hello_agent.logger.logger as log


class PlanAndSolveAgent:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.solver = Solver(self.llm_client)

    def run(self, question: str):
        log.info(f"开始处理问题:\n问题: {question}")
        plan = self.planner.plan(question)
        if not plan:
            log.error("无法生成有效的行动计划。")
            return
        final_answer = self.solver.execute(question, plan)
        log.success(f"任务完成，最终答案: {final_answer}")

# --- 5. 主函数入口 ---
if __name__ == '__main__':
    try:
        llm_client = HelloAgentsLLM()
        agent = PlanAndSolveAgent(llm_client)
        question = "一个水果店周一卖出5544656个苹果。周二卖出的苹果数量是周一的45倍。周三卖出的数量比周二少了509988个。请问这三天总共卖出了多少个苹果？"
        agent.run(question)
    except ValueError as e:
        log.error(str(e))
