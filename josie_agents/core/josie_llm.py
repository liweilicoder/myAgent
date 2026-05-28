import os
from typing import Optional
from openai import OpenAI
from josie_agents.core.base_llm import BaseLLM
import josie_agents.utils.log as log

class JosieLLM(BaseLLM):
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider : Optional[str] = "minimax",
        **kwargs
    ):

        #特殊provider的处理逻辑
        if provider == "modelscope":
            log.info("正在使用自定义的 ModelScope Provider")
            self.provider = "modelscope"

            # 解析 ModelScope 的凭证
            self.api_key = api_key or os.getenv("MODELSCOPE_API_KEY")
            self.base_url = base_url or "https://api-inference.modelscope.cn/v1/"

            # 验证凭证是否存在
            if not self.api_key:
                raise ValueError("ModelScope API key not found. Please set MODELSCOPE_API_KEY environment variable.")

            # 设置默认模型和其他参数
            self.model = model or os.getenv("LLM_MODEL_ID") or "Qwen/Qwen2.5-VL-72B-Instruct"
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens')
            self.timeout = kwargs.get('timeout', 60)

            # 使用获取的参数创建OpenAI客户端实例
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

        elif provider == "ollama":
            log.info("正在使用本地的OLLAMA Provider")
            self.provider = "ollama"

            self.api_key = api_key or os.getenv("OLLAMA_API_KEY")
            self.base_url = base_url or os.getenv("OLLAMA_BASE_URL")

            # 设置默认模型和其他参数
            self.model = model or os.getenv("OLLAMA_MODEL_ID")
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens')
            self.timeout = kwargs.get('timeout', 60)

            # 使用获取的参数创建OpenAI客户端实例
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

        elif provider == "vllm":
            log.info("正在使用本地的VLLM Provider")
            self.provider = "vllm"

            self.api_key = api_key or os.getenv("VLLM_API_KEY")
            self.base_url = base_url or os.getenv("VLLM_BASE_URL")

            # 设置默认模型和其他参数
            self.model = model or os.getenv("VLLM_MODEL_ID")
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens')
            self.timeout = kwargs.get('timeout', 60)

            # 使用获取的参数创建OpenAI客户端实例
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

        elif provider == "minimax":
            log.info("正在使用MiniMax Provider")
            self.provider = "minimax"

            # 解析 MiniMax 的凭证
            self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
            self.base_url = base_url or os.getenv("MINIMAX_BASE_URL")

            # 验证凭证是否存在
            if not self.api_key:
                raise ValueError("MiniMax API key not found. Please set MINIMAX_API_KEY environment variable.")

            # 设置默认模型和其他参数
            self.model = model or os.getenv("MINIMAX_MODEL_ID")
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens')
            self.timeout = kwargs.get('timeout', 60)

            # 使用获取的参数创建OpenAI客户端实例
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)


        else:
            # 非特殊处理逻辑， 直接使用父类BaseModel的初始化逻辑
            super().__init__(model=model, api_key=api_key, base_url=base_url, **kwargs)



# --- 客户端使用示例 ---
if __name__ == '__main__':
    try:
        llmClient = JosieLLM(provider="ollama")

        exampleMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "写一个归并排序算法"}   ]

        log.info("--- 调用LLM ---")
        responseText = llmClient.think(exampleMessages)
        if responseText:
            log.success("--- 完整模型响应 ---")
            log.info(responseText)

    except ValueError as e:
        log.error(e)