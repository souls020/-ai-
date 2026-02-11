"""
用户配置管理
管理 API 设置、风格配置等
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from .styles import StyleManager

# 默认 API 配置
DEFAULT_API_CONFIG = {
    "api_key": "",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 2048,
    "system_prompt": "你是一个有用的AI助手。",
}


class Config:
    """用户配置管理"""

    def __init__(self):
        self.config_dir = Path.home() / ".cheapllm"
        self.config_file = self.config_dir / "config.json"
        self.styles_dir = self.config_dir / "styles"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.styles_dir.mkdir(parents=True, exist_ok=True)

    # ── API 配置 ──────────────────────────────────────────

    def load(self) -> Dict[str, Any]:
        """加载完整配置"""
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text(encoding="utf-8"))
                # 用默认值补全缺失的字段
                merged = {**DEFAULT_API_CONFIG, **data}
                return merged
            except (json.JSONDecodeError, OSError):
                pass
        return dict(DEFAULT_API_CONFIG)

    def save(self, data: Dict[str, Any]):
        """保存完整配置"""
        self.config_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def get(self, key: str, default: Any = None) -> Any:
        """获取单个配置项"""
        data = self.load()
        return data.get(key, default)

    def set(self, key: str, value: Any):
        """设置单个配置项"""
        data = self.load()
        # 自动转换类型
        if key in ("temperature",):
            value = float(value)
        elif key in ("max_tokens",):
            value = int(value)
        data[key] = value
        self.save(data)

    def get_api_config(self) -> Dict[str, Any]:
        """获取 API 配置（用于创建 LLMClient）"""
        return self.load()

    def is_configured(self) -> bool:
        """检查是否已配置 API（至少设置了 api_key 或使用本地模型）"""
        data = self.load()
        # 如果是本地 Ollama 则不需要 api_key
        if "localhost" in data.get("base_url", "") or "127.0.0.1" in data.get("base_url", ""):
            return True
        return bool(data.get("api_key", ""))

    # ── 风格配置 ──────────────────────────────────────────

    def get_style_path(self, name: str) -> Path:
        """获取自定义风格文件路径"""
        return self.styles_dir / f"{name}.json"

    def list_styles(self) -> Dict[str, Dict]:
        """列出所有风格（内置 + 自定义）"""
        manager = StyleManager()
        styles = manager.list_styles()

        for f in self.styles_dir.glob("*.json"):
            if f.stem not in styles:
                try:
                    config = json.loads(f.read_text(encoding="utf-8"))
                    styles[f.stem] = {
                        "description": config.get("description", ""),
                        "author": config.get("author", ""),
                        "custom": True,
                    }
                except (json.JSONDecodeError, OSError):
                    continue

        return styles

    def save_style(self, name: str, config: Dict[str, Any]) -> Path:
        """保存自定义风格配置"""
        path = self.get_style_path(name)
        path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
