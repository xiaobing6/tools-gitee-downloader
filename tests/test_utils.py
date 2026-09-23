"""工具函数纯逻辑测试（零网络）"""

from pathlib import Path

import pytest

from gitee_downloader.utils import (
    build_headers,
    format_file_size,
    is_already_downloaded,
)


def test_format_file_size_boundaries() -> None:
    """format_file_size 边界值"""
    assert format_file_size(0) == "0 B"
    assert format_file_size(1) == "1 B"
    assert format_file_size(1023) == "1023 B"
    assert format_file_size(1024) == "1.0 KB"
    assert format_file_size(1536) == "1.5 KB"
    assert format_file_size(1024 * 1024) == "1.0 MB"
    assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
    assert format_file_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"
    assert format_file_size(1024 * 1024 * 1024 * 1024 * 1024) == "1024.0 TB"


def test_format_file_size_rejects_negative() -> None:
    """负数大小必须报错"""
    with pytest.raises(ValueError):
        format_file_size(-1)


def test_is_already_downloaded(tmp_path: Path) -> None:
    """存在且大小 > 0 才算已下载"""
    missing = tmp_path / "missing.bin"
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")
    real = tmp_path / "real.bin"
    real.write_bytes(b"data")

    assert is_already_downloaded(missing) is False
    assert is_already_downloaded(empty) is False
    assert is_already_downloaded(real) is True


def test_build_headers() -> None:
    """build_headers：有 token 带 PRIVATE-TOKEN，无 token 为空"""
    assert build_headers("tok") == {"PRIVATE-TOKEN": "tok"}
    assert build_headers("") == {}
