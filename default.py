"""默认风格配置"""

default_style = {
    "description": "默认代码风格 - 简洁实用",
    "author": "cheapllm",
    "docstring": "google",
    "comment": "full",
    "naming": {
        "file": "{name}.py",
        "prompt": "{name}_prompt",
    },
    "templates": {
        "prompt": "prompt.j2",
        "agent": "agent.j2",
    },
}
