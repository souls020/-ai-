"""风格管理器"""

import json
from pathlib import Path
from typing import Dict, Any
from .default import default_style


class StyleManager:
    """风格配置管理器 - 统一管理内置风格和 JSON 风格文件"""

    def __init__(self):
        self.styles_dir = Path(__file__).parent

    def get_style(self, name: str) -> Dict[str, Any]:
        """获取指定风格配置

        Args:
            name: 风格名称

        Returns:
            风格配置字典
        """
        if name == "default":
            return default_style

        # 尝试从 JSON 文件加载
        style_file = self.styles_dir / f"{name}.json"
        if style_file.exists():
            try:
                return json.loads(style_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        # 找不到指定风格时回退到默认风格
        return default_style

    def list_styles(self) -> Dict[str, Dict]:
        """列出所有可用的内置风格

        Returns:
            风格名称到描述信息的映射
        """
        styles = {
            "default": {
                "description": default_style["description"],
                "author": default_style.get("author", ""),
            }
        }

        # 扫描 JSON 风格文件
        for f in self.styles_dir.glob("*.json"):
            if f.stem != "default":
                try:
                    config = json.loads(f.read_text(encoding="utf-8"))
                    styles[f.stem] = {
                        "description": config.get("description", ""),
                        "author": config.get("author", ""),
                    }
                except (json.JSONDecodeError, OSError):
                    continue

        return styles
