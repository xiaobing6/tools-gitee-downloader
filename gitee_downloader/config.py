"""配置管理模块"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Config:
    """应用配置类"""

    # Gitee API 配置
    base_url: str = "https://gitee.com/api/v5"
    default_token: str = "bd7ab6529634508be431733a2cc48b60"

    # 默认仓库配置
    default_owner: str = "bio-sense"
    default_repo: str = "icp-monitoring-app"
    default_output_dir: str = "./downloads"

    # 网络配置
    timeout: int = 30
    download_timeout: int = 60
    chunk_size: int = 8192

    # 下载配置
    file_filter: str = "*"
    auto_extract: bool = True
    auto_rename: bool = True

    @classmethod
    def from_args(cls, args) -> "Config":
        """从命令行参数创建配置"""
        config = cls()
        if hasattr(args, 'owner') and args.owner:
            config.default_owner = args.owner
        if hasattr(args, 'repo') and args.repo:
            config.default_repo = args.repo
        if hasattr(args, 'output_dir') and args.output_dir:
            config.default_output_dir = args.output_dir
        if hasattr(args, 'file_filter') and args.file_filter:
            config.file_filter = args.file_filter
        return config

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """
        从配置文件加载配置

        支持 YAML (.yml, .yaml) 和 JSON (.json) 格式

        Args:
            config_path: 配置文件路径

        Returns:
            Config 实例
        """
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        config = cls()
        content = config_path.read_text(encoding="utf-8")
        suffix = config_path.suffix.lower()

        if suffix in (".yaml", ".yml"):
            data = cls._load_yaml(content)
        elif suffix == ".json":
            data = json.loads(content)
        else:
            raise ValueError(f"不支持的配置文件格式: {suffix}，请使用 .yaml, .yml 或 .json")

        # 应用配置
        config._apply_dict(data)
        return config

    @staticmethod
    def _load_yaml(content: str) -> Dict[str, Any]:
        """加载 YAML 内容"""
        try:
            import yaml
            return yaml.safe_load(content) or {}
        except ImportError:
            raise ImportError(
                "读取 YAML 配置文件需要 PyYAML 库，请安装: pip install pyyaml"
            )

    def _apply_dict(self, data: Dict[str, Any]) -> None:
        """从字典应用配置"""
        # 映射关系：配置文件键名 -> 属性名
        mappings = {
            "base_url": "base_url",
            "token": "default_token",
            "owner": "default_owner",
            "repo": "default_repo",
            "output_dir": "default_output_dir",
            "timeout": "timeout",
            "download_timeout": "download_timeout",
            "chunk_size": "chunk_size",
            "file_filter": "file_filter",
            "auto_extract": "auto_extract",
            "auto_rename": "auto_rename",
        }

        for config_key, attr_name in mappings.items():
            if config_key in data:
                value = data[config_key]
                # 类型转换
                if attr_name in ("timeout", "download_timeout", "chunk_size"):
                    value = int(value)
                elif attr_name in ("auto_extract", "auto_rename"):
                    value = bool(value)
                setattr(self, attr_name, value)

    @classmethod
    def find_config_file(cls, search_dir: Path = None) -> Optional[Path]:
        """
        自动查找配置文件

        按优先级查找以下文件：
        1. gitee-downloader.yaml
        2. gitee-downloader.yml
        3. gitee-downloader.json
        4. .gitee-downloader.yaml
        5. .gitee-downloader.yml
        6. .gitee-downloader.json

        Args:
            search_dir: 搜索目录，默认为当前工作目录

        Returns:
            找到的配置文件路径，未找到返回 None
        """
        if search_dir is None:
            search_dir = Path.cwd()

        candidates = [
            "gitee-downloader.yaml",
            "gitee-downloader.yml",
            "gitee-downloader.json",
            ".gitee-downloader.yaml",
            ".gitee-downloader.yml",
            ".gitee-downloader.json",
        ]

        for name in candidates:
            config_path = search_dir / name
            if config_path.exists():
                return config_path

        return None

    def get_token(self, args_token: Optional[str] = None) -> str:
        """
        按优先级获取 token:
        1. 命令行参数
        2. 环境变量 GITEE_TOKEN
        3. 配置文件中的值
        4. 内置默认值
        """
        if args_token:
            return args_token
        env_token = os.environ.get("GITEE_TOKEN")
        if env_token:
            return env_token
        return self.default_token

    def get_output_dir(self, args_output_dir: Optional[str] = None) -> Path:
        """获取输出目录"""
        output_dir = Path(args_output_dir or self.default_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            "base_url": self.base_url,
            "token": self.default_token,
            "owner": self.default_owner,
            "repo": self.default_repo,
            "output_dir": self.default_output_dir,
            "timeout": self.timeout,
            "download_timeout": self.download_timeout,
            "chunk_size": self.chunk_size,
            "file_filter": self.file_filter,
            "auto_extract": self.auto_extract,
            "auto_rename": self.auto_rename,
        }

    def save_to_file(self, config_path: Path, format: str = "yaml") -> None:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径
            format: 文件格式，"yaml" 或 "json"
        """
        data = self.to_dict()

        if format in ("yaml", "yml"):
            try:
                import yaml
                content = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
            except ImportError:
                raise ImportError("保存 YAML 配置文件需要 PyYAML 库，请安装: pip install pyyaml")
        else:
            content = json.dumps(data, indent=2, ensure_ascii=False)

        config_path.write_text(content, encoding="utf-8")
