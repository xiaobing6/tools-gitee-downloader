"""Config 纯逻辑测试（零网络）"""

from pathlib import Path

import pytest

from gitee_downloader.config import Config


def test_from_file_loads_yaml(tmp_path: Path) -> None:
    """YAML 文件能被正确加载并映射到 Config 字段"""
    config_file = tmp_path / "gitee-downloader.yaml"
    config_file.write_text(
        "base_url: https://gitee.com/api/v5\n"
        "token: real-token\n"
        "owner: my-owner\n"
        "repo: my-repo\n"
        "output_dir: ./out\n"
        "timeout: 15\n"
        "file_filter: \"*.tar.gz\"\n"
        "auto_extract: false\n",
        encoding="utf-8",
    )

    config = Config.from_file(config_file)

    assert config.default_token == "real-token"
    assert config.default_owner == "my-owner"
    assert config.default_repo == "my-repo"
    assert config.default_output_dir == "./out"
    assert config.timeout == 15
    assert config.file_filter == "*.tar.gz"
    assert config.auto_extract is False


def test_from_file_rejects_json(tmp_path: Path) -> None:
    """JSON 配置已删除，传入 .json 应报错"""
    config_file = tmp_path / "gitee-downloader.json"
    config_file.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError):
        Config.from_file(config_file)


def test_token_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """优先级：命令行 > 环境变量 > 配置文件 > 空"""
    config_file = tmp_path / "gitee-downloader.yaml"
    config_file.write_text("token: file-token\n", encoding="utf-8")
    config = Config.from_file(config_file)

    monkeypatch.setenv("GITEE_TOKEN", "env-token")
    assert config.get_token("cli-token") == "cli-token"
    assert config.get_token(None) == "env-token"

    monkeypatch.delenv("GITEE_TOKEN")
    assert config.get_token(None) == "file-token"

    empty_config = Config()
    assert empty_config.get_token(None) == ""


def test_placeholder_token_treated_as_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """YOUR_GITEE_TOKEN 占位符按未配置处理"""
    monkeypatch.delenv("GITEE_TOKEN", raising=False)
    config = Config()
    config.default_token = "YOUR_GITEE_TOKEN"
    assert config.get_token(None) == ""

    monkeypatch.setenv("GITEE_TOKEN", "YOUR_GITEE_TOKEN")
    assert config.get_token(None) == ""


def test_find_config_file_in_tmp_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """find_config_file 在指定/当前目录按优先级查找"""
    monkeypatch.chdir(tmp_path)
    assert Config.find_config_file() is None

    (tmp_path / "gitee-downloader.yaml").write_text("owner: a\n", encoding="utf-8")
    assert Config.find_config_file() == tmp_path / "gitee-downloader.yaml"

    (tmp_path / "gitee-downloader.yml").write_text("owner: b\n", encoding="utf-8")
    assert Config.find_config_file() == tmp_path / "gitee-downloader.yaml"

    (tmp_path / "gitee-downloader.yaml").unlink()
    assert Config.find_config_file() == tmp_path / "gitee-downloader.yml"


def test_command_line_overrides_file_config(tmp_path: Path) -> None:
    """命令行参数能覆盖文件配置（merge 单一路径）"""
    from gitee_downloader.__main__ import merge_config_with_args

    config_file = tmp_path / "gitee-downloader.yaml"
    config_file.write_text(
        "owner: file-owner\nrepo: file-repo\noutput_dir: ./file-out\nfile_filter: \"*.zip\"\n",
        encoding="utf-8",
    )
    config = Config.from_file(config_file)

    args = type("Args", (), {})()
    args.owner = "cli-owner"
    args.repo = None
    args.output_dir = "./cli-out"
    args.file_filter = "*.tar.gz"

    merged = merge_config_with_args(config, args)

    assert merged.default_owner == "cli-owner"
    assert merged.default_repo == "file-repo"
    assert merged.default_output_dir == "./cli-out"
    assert merged.file_filter == "*.tar.gz"


def test_save_to_file_roundtrip(tmp_path: Path) -> None:
    """保存 YAML 后可重新加载，且不含已删除的 auto_rename"""
    config = Config()
    config.default_token = "saved-token"
    target = tmp_path / "out.yaml"
    config.save_to_file(target, format="yaml")

    text = target.read_text(encoding="utf-8")
    assert "auto_rename" not in text
    assert "saved-token" in text

    reloaded = Config.from_file(target)
    assert reloaded.default_token == "saved-token"
