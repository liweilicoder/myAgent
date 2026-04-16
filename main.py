import agent.simple_agent.agent_loop as agent
import agent.logger as log

def main():
    log.info("启动旅行助手 Agent")
    agent.chat("你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。")

if __name__ == "__main__":
    main()
