"""cheapllm 命令行入口"""

import click
from .config import Config
from .llm import LLMClient, PROVIDERS


@click.group()
@click.version_option(version="0.2.0", prog_name="cheapllm")
@click.pass_context
def cli(ctx: click.Context):
    """cheapllm - 廉价、可定制的大语言模型开发工具

    \b
    快速开始:
      1. cheapllm init                    # 初始化配置
      2. cheapllm ask "什么是Python?"      # 提问
      3. cheapllm chat                    # 交互式对话
    """
    ctx.ensure_object(dict)


# ── 核心功能：对话 ──────────────────────────────────────────


@cli.command("init")
def init_config():
    """交互式初始化配置（选择服务商、填写 API Key）"""
    config = Config()

    click.echo("🚀 欢迎使用 cheapllm！让我们来配置你的 LLM 服务。\n")

    # 列出服务商
    click.echo("可用的 LLM 服务商：")
    provider_names = list(PROVIDERS.keys())
    for i, (name, info) in enumerate(PROVIDERS.items(), 1):
        click.echo(f"  {i}. {name:15s} - {info['description']}")
    click.echo(f"  {len(provider_names) + 1}. {'custom':15s} - 自定义 OpenAI 兼容 API")

    # 选择服务商
    choice = click.prompt(
        "\n请选择服务商编号",
        type=int,
        default=1,
    )

    if 1 <= choice <= len(provider_names):
        provider = provider_names[choice - 1]
        info = PROVIDERS[provider]
        base_url = info["base_url"]
        model = info["model"]
        click.echo(f"\n已选择: {provider} ({info['description']})")
    else:
        base_url = click.prompt("请输入 API Base URL", default="https://api.openai.com/v1")
        model = click.prompt("请输入模型名称", default="gpt-3.5-turbo")

    # API Key
    is_local = "localhost" in base_url or "127.0.0.1" in base_url
    if is_local:
        api_key = ""
        click.echo("(本地模型，无需 API Key)")
    else:
        api_key = click.prompt("\n请输入 API Key", hide_input=True)

    # 保存配置
    config.set("base_url", base_url)
    config.set("model", model)
    config.set("api_key", api_key)

    click.echo(f"\n✅ 配置已保存到 {config.config_file}")
    click.echo(f"   服务地址: {base_url}")
    click.echo(f"   模型: {model}")
    click.echo(f"\n现在可以使用以下命令：")
    click.echo(f'   cheapllm ask "你好"       # 快速提问')
    click.echo(f"   cheapllm chat             # 交互式对话")


@cli.command("ask")
@click.argument("question")
@click.option("--model", "-m", default=None, help="指定模型（覆盖配置）")
@click.option("--no-stream", is_flag=True, help="关闭流式输出")
def ask(question: str, model: str, no_stream: bool):
    """快速提问（单轮对话）

    \b
    示例:
      cheapllm ask "什么是Python?"
      cheapllm ask "翻译成英文：你好世界" -m gpt-4
    """
    config = Config()
    _check_configured(config)

    api_config = config.get_api_config()
    if model:
        api_config["model"] = model

    client = LLMClient.from_config(api_config)

    if not no_stream:
        # 流式输出模式
        client.ask(question, stream=True)
    else:
        reply = client.ask(question, stream=False)
        click.echo(reply)


@cli.command("chat")
@click.option("--model", "-m", default=None, help="指定模型")
@click.option("--system", "-s", default=None, help="系统提示词")
def chat(model: str, system: str):
    """交互式多轮对话

    \b
    对话中的特殊命令:
      /clear  清空对话历史
      /model  查看当前模型
      /exit   退出对话（也可用 Ctrl+C）
    """
    config = Config()
    _check_configured(config)

    api_config = config.get_api_config()
    if model:
        api_config["model"] = model
    if system:
        api_config["system_prompt"] = system

    client = LLMClient.from_config(api_config)

    click.echo(f"💬 cheapllm 对话模式 (模型: {api_config.get('model', '?')})")
    click.echo("   输入 /exit 退出, /clear 清空历史, /model 查看模型\n")

    while True:
        try:
            user_input = click.prompt("你", prompt_suffix=" > ")
        except (EOFError, click.Abort):
            click.echo("\n👋 再见！")
            break

        if not user_input.strip():
            continue

        # 处理特殊命令
        cmd = user_input.strip().lower()
        if cmd in ("/exit", "/quit", "/q"):
            click.echo("👋 再见！")
            break
        elif cmd == "/clear":
            client.clear_history()
            click.echo("🗑️  对话历史已清空\n")
            continue
        elif cmd == "/model":
            click.echo(f"   当前模型: {client.model}")
            click.echo(f"   API 地址: {client.base_url}\n")
            continue

        # 发送消息
        click.echo()
        click.secho("AI > ", nl=False, fg="green")
        try:
            client.chat(user_input, stream=True)
        except RuntimeError as e:
            click.secho(f"\n❌ {e}", fg="red", err=True)
        click.echo()


# ── 配置管理 ──────────────────────────────────────────


@cli.group("config")
def config_group():
    """管理配置（API Key、模型、服务地址等）"""
    pass


@config_group.command("show")
def config_show():
    """查看当前配置"""
    config = Config()
    data = config.load()
    click.echo("当前配置：")
    for key, value in data.items():
        if key == "api_key" and value:
            # 隐藏 API Key 中间部分
            display = value[:8] + "..." + value[-4:] if len(value) > 16 else "****"
        else:
            display = value
        click.echo(f"  {key}: {display}")
    click.echo(f"\n配置文件: {config.config_file}")


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """设置配置项

    \b
    可用配置项:
      api_key        API 密钥
      base_url       API 地址
      model          模型名称
      temperature    生成温度 (0-2)
      max_tokens     最大 Token 数
      system_prompt  系统提示词
    """
    config = Config()
    config.set(key, value)
    display = "****" if key == "api_key" else value
    click.echo(f"✅ 已设置 {key} = {display}")


@config_group.command("providers")
def config_providers():
    """列出支持的 LLM 服务商"""
    click.echo("支持的 LLM 服务商（均兼容 OpenAI 接口）：\n")
    for name, info in PROVIDERS.items():
        click.echo(f"  {name:15s} {info['description']}")
        click.echo(f"  {'':15s} 地址: {info['base_url']}")
        click.echo(f"  {'':15s} 默认模型: {info['model']}")
        click.echo()


# ── 代码生成 ──────────────────────────────────────────


@cli.command("generate-agent")
@click.option("--name", default="my_agent", help="Agent 名称")
@click.option("--desc", default="一个智能助手", help="Agent 描述")
@click.option("--style", default="default", help="代码风格配置")
@click.option("--output", "-o", default=".", help="输出目录")
def generate_agent(name: str, desc: str, style: str, output: str):
    """生成 Agent 类代码（可直接调用 LLM）"""
    from .generator import Generator

    try:
        gen = Generator(style)
        result = gen.generate_agent(name, desc, output)
        click.echo(f"[OK] Agent '{name}' 已生成到 {result}")
    except Exception as e:
        click.echo(f"[ERROR] 生成失败: {e}", err=True)
        raise click.Abort()


@cli.command("generate-prompt")
@click.option("--name", default="my_prompt", help="Prompt 模板名称")
@click.option("--template", required=True, help="Prompt 模板内容")
@click.option("--style", default="default", help="代码风格配置")
@click.option("--output", "-o", default=".", help="输出目录")
def generate_prompt(name: str, template: str, style: str, output: str):
    """生成 Prompt 模板代码"""
    from .generator import Generator

    try:
        gen = Generator(style)
        result = gen.generate_prompt(name, template, output)
        click.echo(f"[OK] Prompt '{name}' 已生成到 {result}")
    except Exception as e:
        click.echo(f"[ERROR] 生成失败: {e}", err=True)
        raise click.Abort()


@cli.command("list-styles")
def list_styles():
    """列出所有可用的代码风格配置"""
    config = Config()
    styles = config.list_styles()
    if not styles:
        click.echo("  没有可用的风格配置")
        return
    for name, info in styles.items():
        desc = info.get("description", "无描述")
        custom = " [自定义]" if info.get("custom") else ""
        click.echo(f"  {name}: {desc}{custom}")


# ── 辅助函数 ──────────────────────────────────────────


def _check_configured(config: Config):
    """检查是否已配置 API"""
    if not config.is_configured():
        click.echo("⚠️  尚未配置 API，请先运行：")
        click.echo("   cheapllm init")
        click.echo("\n或手动设置：")
        click.echo('   cheapllm config set api_key "你的API密钥"')
        click.echo('   cheapllm config set base_url "https://api.deepseek.com/v1"')
        raise click.Abort()


def main():
    cli()


if __name__ == "__main__":
    main()
