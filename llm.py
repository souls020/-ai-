"""
LLM API 客户端
支持所有 OpenAI 兼容接口（OpenAI / DeepSeek / Ollama / 通义千问 等）
使用 Python 标准库，零额外依赖
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Generator


# 预设的常用模型服务商
PROVIDERS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
        "description": "OpenAI 官方 API",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "description": "DeepSeek（性价比高）",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5",
        "description": "Ollama 本地模型（免费）",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
        "description": "智谱 AI（GLM 系列）",
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "description": "SiliconFlow（多模型聚合，有免费额度）",
    },
}


class LLMClient:
    """LLM API 客户端

    支持所有 OpenAI 兼容的 Chat Completions 接口。

    用法:
        client = LLMClient(api_key="sk-xxx", base_url="https://api.deepseek.com/v1")
        reply = client.chat("你好，请介绍一下你自己")
        print(reply)
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: str = "",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.history: List[Dict[str, str]] = []

        if system_prompt:
            self.history.append({"role": "system", "content": system_prompt})

    def _build_messages(self, user_input: str) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = list(self.history)
        messages.append({"role": "user", "content": user_input})
        return messages

    def _call_api(self, messages: List[Dict[str, str]], stream: bool = False) -> dict:
        """调用 Chat Completions API"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                if stream:
                    return self._handle_stream(resp)
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get("error", {}).get("message", error_body)
            except json.JSONDecodeError:
                error_msg = error_body
            raise RuntimeError(f"API 请求失败 (HTTP {e.code}): {error_msg}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"无法连接到 API 服务器 ({self.base_url}): {e.reason}\n"
                f"请检查: 1) 网络连接 2) base_url 是否正确 3) 如果用 Ollama 请确认服务已启动"
            ) from e

    def _handle_stream(self, resp) -> dict:
        """处理流式响应，实时输出并收集完整回复"""
        full_content = ""
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    print(content, end="", flush=True)
                    full_content += content
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
        print()  # 换行
        return {
            "choices": [{"message": {"role": "assistant", "content": full_content}}]
        }

    def chat(self, user_input: str, stream: bool = True) -> str:
        """发送消息并获取回复

        Args:
            user_input: 用户输入
            stream: 是否流式输出（默认 True）

        Returns:
            助手的回复文本
        """
        messages = self._build_messages(user_input)
        result = self._call_api(messages, stream=stream)

        reply = result["choices"][0]["message"]["content"]

        # 保存到历史记录
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": reply})

        return reply

    def ask(self, question: str, stream: bool = True) -> str:
        """单轮问答（不保留历史记录）

        Args:
            question: 问题
            stream: 是否流式输出

        Returns:
            回复文本
        """
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": question})

        result = self._call_api(messages, stream=stream)
        return result["choices"][0]["message"]["content"]

    def clear_history(self):
        """清空对话历史"""
        self.history = []
        if self.system_prompt:
            self.history.append({"role": "system", "content": self.system_prompt})

    @classmethod
    def from_config(cls, config: dict) -> "LLMClient":
        """从配置字典创建客户端"""
        return cls(
            api_key=config.get("api_key", ""),
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            model=config.get("model", "gpt-3.5-turbo"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2048),
            system_prompt=config.get("system_prompt", ""),
        )
