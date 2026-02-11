"""
代码生成器
根据风格配置生成 Prompt 模板和 Agent 类
"""

import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .styles import StyleManager


def to_class_name(name: str) -> str:
    """将名称转换为类名格式

    例如: my_chatbot -> MyChatbot
    """
    return re.sub(r"[_-]", "", name.title())


class Generator:
    """代码生成器"""

    def __init__(self, style_name: str = "default"):
        self.style = StyleManager().get_style(style_name)
        self.template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _get_template(self, template_ref: str):
        """获取模板对象

        如果模板引用是 .j2 文件名，则从文件加载；
        否则作为内联模板字符串处理。

        Args:
            template_ref: 模板文件名或内联模板字符串

        Returns:
            Jinja2 模板对象
        """
        if template_ref.endswith(".j2"):
            return self.env.get_template(template_ref)
        return self.env.from_string(template_ref)

    def generate_prompt(self, name: str, template: str, output: str = ".") -> str:
        """生成 Prompt 模板

        Args:
            name: Prompt 名称
            template: Prompt 模板内容
            output: 输出目录路径

        Returns:
            生成的文件路径
        """
        output_path = Path(output)
        naming = self.style.get("naming", {})
        file_name = naming.get("prompt", "{name}_prompt").format(name=name)
        if not file_name.endswith(".py"):
            file_name += ".py"

        # 渲染模板
        template_ref = self.style["templates"]["prompt"]
        prompt_template = self._get_template(template_ref)
        code = prompt_template.render(
            name=name,
            template_content=template,
            docstring_style=self.style.get("docstring", "google"),
            comment_style=self.style.get("comment", "full"),
        )

        # 写入文件
        output_file = output_path / file_name
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code, encoding="utf-8")

        return str(output_file)

    def generate_agent(self, name: str, desc: str, output: str = ".") -> str:
        """生成 Agent 类

        Args:
            name: Agent 名称
            desc: Agent 描述
            output: 输出目录路径

        Returns:
            生成的文件路径
        """
        output_path = Path(output)
        naming = self.style.get("naming", {})
        class_name = to_class_name(name)
        file_name = naming.get("file", "{name}.py").format(name=name)
        if not file_name.endswith(".py"):
            file_name += ".py"

        # 渲染模板
        template_ref = self.style["templates"]["agent"]
        agent_template = self._get_template(template_ref)
        code = agent_template.render(
            class_name=class_name,
            name=name,
            description=desc,
            docstring_style=self.style.get("docstring", "google"),
            comment_style=self.style.get("comment", "full"),
        )

        # 写入文件
        output_file = output_path / file_name
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code, encoding="utf-8")

        return str(output_file)
