import os
from dotenv import load_dotenv

load_dotenv()

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core.models import ModelInfo

from autogen_team.tools.file_tools import (
    init_output_dirs,
    save_file,
    read_file,
)
from autogen_team.utils.console import print_message

def create_openai_model_client():
    """创建 OpenAI 模型客户端用于测试"""
    return OpenAIChatCompletionClient(
        model=os.getenv("LLM_MODEL_ID"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        model_info=ModelInfo(
            vision=False,
            function_calling=True,
            json_output=True,
            structured_output=True,
            family="minimax"
        ),
        user="jesse",
        include_name_in_message=False,
        add_name_prefixes=False,
    )


def create_product_manager(model_client):
    """创建产品经理智能体"""
    system_message = """你是一位专业的产品经理，擅长需求分析和产品规划。

## 核心职责
1. 深入理解用户需求，识别核心功能和边界条件
2. 制定清晰的技术实现路径
3. 定义明确的验收标准
4. 与工程师有效沟通，协调推进开发

## 分析框架
接到任务后，请按以下结构输出需求分析：
1. **背景**：业务场景和用户痛点
2. **目标**：要解决的核心问题和达成效果
3. **功能列表**：核心功能模块划分
4. **非功能需求**：性能、安全、兼容性等要求
5. **验收标准**：可测试的功能点和完成条件

## 文件操作
- 需求确认后，调用 `save_file` 保存为 `prd.md`
- 后续迭代时，先调用 `read_file` 读取现有文档，基于原文档修改后调用 `save_file` 重新保存


** 重要** 完成后必须说 "需求分析完成，请工程师开始实现"."""

    return AssistantAgent(
        name="ProductManager",
        model_client=model_client,
        system_message=system_message,
        tools=[save_file, read_file],
    )


def create_engineer(model_client):
    """创建软件工程师智能体"""
    system_message = """你是一位专业的 Python 软件工程师，擅长 Web 应用开发。

## 技术要求
1. **代码质量**：清晰可读、模块化、错误处理完善
2. **技术栈**：Python + Streamlit/Flask/Django + 必要依赖
3. **最佳实践**：遵循 PEP8、合理的注释、完善的异常处理

## 开发流程
1. 仔细阅读产品需求文档（PRD）
2. 设计代码结构和模块划分
3. 编写完整的可运行代码
4. 编写 README.md 和 requirements.txt

## 产出文件（必须全部保存）
- **主代码文件**：如 `app.py`、`main.py`
- **requirements.txt**：所有 Python 依赖
- **README.md**：项目说明、运行方式、API 说明

## 文件操作
- 每个文件完成后立即调用 `save_file` 保存
- 可用 `read_file` 查阅已保存的文件

** 重要**  完成后必须说 "代码开发完成，请审查员检查"."""

    return AssistantAgent(
        name="Engineer",
        model_client=model_client,
        system_message=system_message,
        tools=[save_file, read_file],
    )


def create_code_reviewer(model_client):
    """创建代码审查员智能体"""
    system_message = """你是一位专业的代码审查专家，专注于代码质量和安全。

## 审查维度（每项评分 1-10 并说明）
1. **可读性**：命名清晰、结构合理、注释充分
2. **安全性**：输入验证、SQL注入防护、XSS防护、敏感信息处理
3. **性能**：数据库查询效率、算法复杂度、资源占用
4. **可维护性**：模块化程度、代码复用、测试覆盖

## 审查流程
1. 调用 `read_file` 读取工程师提交的文件
2. 对照 PRD 验证功能完整性
3. 逐项评分并给出改进建议
4. 输出优化后的完整代码
5. 调用 `save_file` 保存优化后的代码（直接覆盖）

** 重要**  完成后必须说 "代码审查完成"."""

    return AssistantAgent(
        name="CodeReviewer",
        model_client=model_client,
        system_message=system_message,
        tools=[save_file, read_file],
    )


def create_user_proxy():
    """创建用户代理智能体"""
    return UserProxyAgent(
        name="UserProxy",
        description="""用户代理，负责验证最终实现是否符合需求。

## 职责
1. 接收产品需求文档（PRD）确认功能范围
2. 运行代码验证核心功能是否正常工作
3. 检查是否满足验收标准
4. 提供用户反馈或确认完成

## 测试验证流程
1. 阅读 PRD 确认验收标准
2. 安装依赖：`pip install -r requirements.txt`
3. 启动应用验证功能
4. 测试边界情况和错误处理

## 完成标准
- 所有验收标准已满足
- 代码可正常运行
- 无明显错误或异常

测试通过后回复 TERMINATE.""",
    )


async def run_software_development_team(task, biz, project="."):
    """运行软件开发团队协作"""

    print("🔧 正在初始化模型客户端...")

    model_client = create_openai_model_client()

    output_dirs = init_output_dirs(project, biz)
    print(f"📁 输出目录已创建: {output_dirs}")

    print("👥 正在创建智能体团队...")

    product_manager = create_product_manager(model_client)
    engineer = create_engineer(model_client)
    code_reviewer = create_code_reviewer(model_client)
    user_proxy = create_user_proxy()

    def selector_func(messages: list) -> str | None:
        """根据消息内容决定下一个发言的智能体"""
        if not messages:
            return "ProductManager"

        last_message = messages[-1]
        last_speaker = last_message.source
        content = str(last_message.content).upper()

        # ProductManager 完成后 -> Engineer
        if last_speaker == "ProductManager":
            if "需求分析完成" in content :
                return "Engineer"
            else:
                return "ProductManager"

        # Engineer 完成后 -> CodeReviewer
        if last_speaker == "Engineer":
            if "代码开发完成" in content:
                return "CodeReviewer"
            else:
                return "Engineer"

        # CodeReviewer 完成后 -> UserProxy
        if last_speaker == "CodeReviewer":
            if "代码审查完成" in content:
                return "UserProxy"
            else:
                return "CodeReviewer"

        # UserProxy 完成后终止
        if last_speaker == "UserProxy":
            return None

        return None

    team_chat = SelectorGroupChat(
        model_client=model_client,
        participants=[
            product_manager,
            engineer,
            code_reviewer,
            user_proxy
        ],
        selector_func=selector_func,
        termination_condition=TextMentionTermination("TERMINATE"),
        max_turns=50,
    )

    print("🚀 启动 AutoGen 软件开发团队协作...")
    print("=" * 60)

    result = None
    stream = team_chat.run_stream(task=task)
    async for message in stream:
        await print_message(message)
        result = message

    print("\n" + "=" * 60)
    print("✅ 团队协作完成！")

    return result