"""解压安全与提取逻辑测试（零网络）"""

import tarfile
import zipfile
from pathlib import Path

import pytest

from gitee_downloader.extractor import ArchiveExtractor, PostProcessor


def _make_evil_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("../evil.txt", "pwned")


def _make_evil_tar_gz(path: Path) -> None:
    with tarfile.open(path, "w:gz") as tf:
        evil = tarfile.TarInfo("../evil.txt")
        data = b"pwned"
        evil.size = len(data)
        import io

        tf.addfile(evil, io.BytesIO(data))


def _make_normal_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("topdir/readme.txt", "hello-zip")


def _make_normal_tar_gz(path: Path) -> None:
    with tarfile.open(path, "w:gz") as tf:
        data = b"hello-tar"
        import io

        info = tarfile.TarInfo("topdir/readme.txt")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))


def test_evil_zip_rejected_and_no_escape(tmp_path: Path) -> None:
    """含 ../ 逃逸条目的 zip 必须被拒绝且不写出目标目录"""
    archive = tmp_path / "evil.zip"
    _make_evil_zip(archive)
    out_dir = tmp_path / "out"

    result = ArchiveExtractor().extract(archive, out_dir)

    assert result is None
    assert not (tmp_path / "evil.txt").exists()
    assert not (tmp_path.parent / "evil.txt").exists()


def test_evil_tar_gz_rejected_and_no_escape(tmp_path: Path) -> None:
    """含 ../ 逃逸条目的 tar.gz 必须被拒绝且不写出目标目录"""
    archive = tmp_path / "evil.tar.gz"
    _make_evil_tar_gz(archive)
    out_dir = tmp_path / "out"

    result = ArchiveExtractor().extract(archive, out_dir)

    assert result is None
    assert not (tmp_path / "evil.txt").exists()
    assert not (tmp_path.parent / "evil.txt").exists()


def test_safe_target_path_rejects_escape(tmp_path: Path) -> None:
    """_safe_target_path 直接拒绝逃逸路径"""
    with pytest.raises(ValueError):
        ArchiveExtractor._safe_target_path(tmp_path, "../evil.txt")


def test_normal_zip_extracts_and_flattens(tmp_path: Path) -> None:
    """正常 zip 能解压，且单顶层目录被展平"""
    archive = tmp_path / "pkg.zip"
    _make_normal_zip(archive)
    out_dir = tmp_path / "out"

    target = ArchiveExtractor().extract(archive, out_dir)

    assert target == out_dir / "pkg"
    assert (out_dir / "pkg" / "readme.txt").read_text(encoding="utf-8") == "hello-zip"


def test_normal_tar_gz_extracts_and_flattens(tmp_path: Path) -> None:
    """正常 tar.gz 能解压，且单顶层目录被展平"""
    archive = tmp_path / "pkg.tar.gz"
    _make_normal_tar_gz(archive)
    out_dir = tmp_path / "out"

    target = ArchiveExtractor().extract(archive, out_dir)

    assert target == out_dir / "pkg"
    assert (out_dir / "pkg" / "readme.txt").read_bytes() == b"hello-tar"


def test_unsupported_format_returns_none(tmp_path: Path) -> None:
    """不支持的格式返回 None"""
    archive = tmp_path / "pkg.rar"
    archive.write_bytes(b"x")

    assert ArchiveExtractor().extract(archive, tmp_path / "out") is None


def test_post_processor_skips_already_extracted(tmp_path: Path) -> None:
    """已解压目录会被 PostProcessor 跳过（is_already_extracted 逻辑仍生效）"""
    archive = tmp_path / "pkg.zip"
    _make_normal_zip(archive)
    out_dir = tmp_path / "out"
    processor = PostProcessor()

    first = processor.process(archive, out_dir)
    assert first == out_dir / "pkg"
    (out_dir / "pkg" / "marker.txt").write_text("m", encoding="utf-8")

    # 目录已存在且非空、修改时间不旧于压缩包 -> 跳过解压
    second = processor.process(archive, out_dir)
    assert second == out_dir / "pkg"
