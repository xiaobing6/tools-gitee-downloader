"""CLI 入口纯逻辑测试（零网络）"""

import sys
from pathlib import Path

import pytest

from gitee_downloader.__main__ import load_config, parse_arguments


def test_parse_arguments_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """默认值：除 --config/--init-config 外均为 None/False"""
    monkeypatch.setattr(sys, "argv", ["gitee-downloader"])
    args = parse_arguments()

    assert args.config is None
    assert args.init_config is False
    assert args.owner is None
    assert args.repo is None
    assert args.token is None
    assert args.output_dir is None
    assert args.file_filter is None
    assert args.tag is None


def test_parse_arguments_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """命令行参数覆盖默认值"""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "gitee-downloader",
            "--owner",
            "o",
            "--repo",
            "r",
            "--token",
            "t",
            "--output-dir",
            "./out",
            "--file-filter",
            "*.tar.gz",
            "--tag",
            "v1.0.0",
        ],
    )
    args = parse_arguments()

    assert args.owner == "o"
    assert args.repo == "r"
    assert args.token == "t"
    assert args.output_dir == "./out"
    assert args.file_filter == "*.tar.gz"
    assert args.tag == "v1.0.0"


def test_help_examples_use_console_script() -> None:
    """帮助文本示例统一使用 gitee-downloader，不再出现 python main.py 和 exe 分支"""
    import gitee_downloader.__main__ as entry

    source = Path(entry.__file__).read_text(encoding="utf-8")
    assert "gitee-downloader --init-config" in source
    assert "python main.py" not in source
    assert "sys.path.insert" not in source


def test_load_config_missing_file_exits(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """--config 指向不存在的文件时以退出码 1 结束"""
    monkeypatch.chdir(tmp_path)
    args = type("Args", (), {})()
    args.config = str(tmp_path / "not-exist.yaml")

    with pytest.raises(SystemExit) as exc_info:
        load_config(args)

    assert exc_info.value.code == 1


def test_load_config_finds_local_yaml(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """未指定 --config 时自动查找当前目录的 gitee-downloader.yaml"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "gitee-downloader.yaml").write_text("owner: local\n", encoding="utf-8")
    args = type("Args", (), {})()
    args.config = None

    config = load_config(args)

    assert config.default_owner == "local"


def test_load_config_defaults_when_no_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """无配置文件时回退到内置默认值"""
    monkeypatch.chdir(tmp_path)
    args = type("Args", (), {})()
    args.config = None

    config = load_config(args)

    assert config.default_owner == "bio-sense"
    assert config.default_repo == "icp-monitoring-app"
