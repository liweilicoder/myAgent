import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Iterator, Optional

import josie_agents.utils.log as log
from josie_agents.utils.trim import clean_llm_resp

# 加载 .env 文件中的环境变量
load_dotenv()


class BaseLLM:
    """
    父类 LLM 调用Client
    它用于调用任何兼容OpenAI接口的服务，并默认使用流式响应。
    """

    def __init__(self, model: str = None, api_key: str = None, base_url: str = None, **kwargs):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。
        """

        log.info("正在使用 Default Provider")

        self.model = model or os.getenv("LLM_MODEL_ID")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")

        self.temperature = kwargs.get('temperature', 0)
        self.max_tokens = kwargs.get('max_tokens')
        self.timeout = kwargs.get('timeout', 60)

        if not all([self.model, self.api_key, self.base_url]):
            raise ValueError("模型ID、API密钥和服务地址必须被提供或在.env文件中定义。")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def think(self, messages: List[Dict[str, str]], temperature: Optional[float] = None) -> Iterator[str]:
        """
        调用大语言模型进行思考，并返回其响应。
        这是主要的调用方法，默认使用流式响应以获得更好的用户体验。
        """
        log.info(f"🧠 正在【流式】调用 {self.model} 模型...")
        log.debug(f" ➡️ 模型输入:")
        for i, m in enumerate(messages):
            log.debug(f"role={m['role']}, content={m['content']}",True)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
                if temperature is not None
                else self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )

            # 处理流式响应
            log.debug("⬅️ 模型输出:")
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                log.stream(content)
                yield content
            log.line_break()

        except Exception as e:
            log.error(f"❌ 调用LLM API时发生错误: {e}")
            return ""

    def invoke(self, messages: list[dict[str, str]], trim_think: bool=False, **kwargs) -> str:
        """
        非流式调用LLM，返回完整响应。
        适用于不需要流式输出的场景。
        """
        log.info(f"🧠 正在【非流式】调用 {self.model} 模型...")
        log.debug(f" ➡️ 模型输入:")
        for i, m in enumerate(messages):
            log.debug(f"role={m['role']}, content={m['content']}", True)


        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["temperature", "max_tokens"]
                },
            )

            content = response.choices[0].message.content
            log.debug("⬅️ 模型输出:")
            log.debug(content)

            if trim_think:
                content = clean_llm_resp(content)

            return content

        except Exception as e:
            log.error(f"❌ 调用LLM API时发生错误: {e}")
            return ""


# --- 客户端使用示例 ---
if __name__ == '__main__':
    try:
        llmClient = BaseLLM()

        invokeMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "写一个快速排序算法"}
        ]

        responseText = llmClient.invoke(invokeMessages)

        thinkMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "写一个归并排序算法"}
        ]

        for content in llmClient.think(thinkMessages):
            pass


    except ValueError as e:
        log.error(e)