import traceback
import asyncio

from autogen_team.software_team import run_software_development_team

# 定义开发任务
task = """我们需要开发一个人民币到美元/日元/英镑等货币的汇率显示应用，具体要求如下：

核心功能：
- 实时显示当前汇率
- 显示24小时汇率变化趋势（涨跌幅和涨跌额）
- 提供汇率刷新功能

技术要求：
- 使用 Streamlit 框架创建 Web 应用
- 界面简洁美观，用户友好
- 添加适当的错误处理和加载状态

请团队协作完成这个任务，从需求分析到最终实现。"""

# 主程序入口
if __name__ == "__main__":
    try:
        # 运行异步协作流程
        result = asyncio.run(run_software_development_team(task, "exchange_app"))

        print(f"\n📋 协作结果摘要：")
        print(f"- 参与智能体数量：4个")
        print(f"- 任务完成状态：{'成功' if result else '需要进一步处理'}")

    except ValueError as e:
        print(f"❌ 配置错误：{e}")
        print("请检查 .env 文件中的配置是否正确")
    except Exception as e:
        print(f"❌ 运行错误：{e}")
        traceback.print_exc()
