"""
多Agent协作的智能文档助手

使用两个SimpleAgent分工协作：
- Agent1：GitHub搜索专家
- Agent2：文档生成专家
"""

from dotenv import load_dotenv
from josie_agents.agents.josie_simple_agent import JosieSimpleAgent
from josie_agents.core.josie_llm import JosieLLM
from josie_agents.tools.builtin.protocol_tools import MCPTool
from josie_agents.utils import log
import os

load_dotenv()

def main():
    log.delimiter("多Agent协作的智能文档助手")

    # ============================================================
    # Agent 1: GitHub搜索专家
    # ============================================================
    log.delimiter("【步骤1】创建GitHub搜索专家...")

    github_searcher = JosieSimpleAgent(
        name="GitHub搜索专家",
        llm=JosieLLM(),
        system_prompt="""你是一个GitHub搜索专家。
    你的任务是搜索GitHub仓库并返回结果。
    请返回清晰、结构化的搜索结果，包括：
    - 仓库名称
    - 简短描述

    保持简洁，不要添加额外的解释。"""
    )

    # 添加GitHub工具
    github_tool = MCPTool(
        name ="gh",
        server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
    )
    github_searcher.add_tool(github_tool)

    # ============================================================
    # Agent 2: 文档生成专家
    # ============================================================
    log.delimiter("【步骤2】创建文档生成专家...")

    document_writer = JosieSimpleAgent(
        name="文档生成专家",
        llm=JosieLLM(),
        system_prompt="""你是一个文档生成专家。
    你的任务是根据提供的信息生成结构化的Markdown报告并使用工具将结果保存。

    报告应该包括：
    - 标题
    - 简介
    - 主要内容（分点列出，包括项目名称、描述等）
    - 总结

    请直接把完整的Markdown格式文件保存。"""
    )

    # 添加文件系统工具
    fs_tool = MCPTool(
        name="fs",
        server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "./test_data"]
    )
    document_writer.add_tool(fs_tool)


    # 步骤1：GitHub搜索
    log.delimiter("【步骤3】Agent1 搜索GitHub...")
    search_task = "搜索关于'AI agent'的GitHub仓库，返回前5个最相关的结果"

    search_results = github_searcher.run(search_task)

    log.test(f"搜索结果:\n {search_results}")

    # 步骤2：生成报告
    log.test("【步骤4】Agent2 生成报告...")
    report_task = f"""
    根据以下GitHub搜索结果，生成一份Markdown格式的研究报告：

    {search_results}

    报告要求：
    1. 标题：# AI Agent框架研究报告
    2. 简介：说明这是关于AI Agent的GitHub项目调研
    3. 主要发现：列出找到的项目及其特点（包括名称、描述等）
    4. 总结：总结这些项目的共同特点

    将报告保存在./test_data/report.md文件中。
    """

    report_content = document_writer.run(report_task)

    log.test(f"报告内容:\n {report_content}")



if __name__ == "__main__":
    main()