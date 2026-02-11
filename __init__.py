"""cheapllm - 廉价、可定制的大语言模型开发工具"""

__version__ = "0.2.0"

from .llm import LLMClient
from .config import Config

__all__ = ["LLMClient", "Config", "__version__"]
