# cheapllm

廉价、可定制的大语言模型开发工具。

支持所有 OpenAI 兼容接口（OpenAI / DeepSeek / Ollama / 通义千问 / SiliconFlow 等）。

## 快速开始

### 安装

```bash
pip install -e .
```

### 初始化配置

```bash
cheapllm init
```

交互式选择服务商并填写 API Key。

### 直接提问

```bash
cheapllm ask "什么是Python?"
cheapllm ask "翻译成英文：你好世界" -m gpt-4
```

### 交互式对话

```bash
cheapllm chat
cheapllm chat -m deepseek-chat -s "你是一个翻译官"
```

## 所有命令

| 命令 | 说明 |
|------|------|
| `cheapllm init` | 交互式初始化配置 |
| `cheapllm ask "问题"` | 快速提问（单轮） |
| `cheapllm chat` | 交互式多轮对话 |
| `cheapllm config show` | 查看当前配置 |
| `cheapllm config set KEY VALUE` | 修改配置项 |
| `cheapllm config providers` | 列出支持的服务商 |
| `cheapllm generate-agent` | 生成 Agent 类代码 |
| `cheapllm generate-prompt` | 生成 Prompt 模板代码 |
| `cheapllm list-styles` | 列出可用代码风格 |

## 配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `api_key` | API 密钥 | (空) |
| `base_url` | API 地址 | `https://api.openai.com/v1` |
| `model` | 模型名称 | `gpt-3.5-turbo` |
| `temperature` | 生成温度 | `0.7` |
| `max_tokens` | 最大 Token 数 | `2048` |
| `system_prompt` | 系统提示词 | `你是一个有用的AI助手。` |

## 支持的服务商

| 服务商 | 说明 |
|--------|------|
| OpenAI | 官方 API |
| DeepSeek | 性价比高 |
| Ollama | 本地模型（免费） |
| 智谱 AI | GLM 系列 |
| SiliconFlow | 多模型聚合，有免费额度 |

或任何兼容 OpenAI 接口的服务。

## 作为 Python 库使用

```python
from cheapllm import LLMClient

client = LLMClient(
    api_key="sk-xxx",
    base_url="https://api.deepseek.com/v1",
    model="deepseek-chat",
)

reply = client.chat("你好！", stream=False)
print(reply)
```

## License

MIT
