"""文件解压和重命名模块"""

import re
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import List, Literal, Optional, Tuple

from .utils import Logger


class ArchiveExtractor:
    """压缩包提取器"""

    # 支持的压缩格式
    SUPPORTED_FORMATS = {
        ".zip": "zip",
        ".tar.gz": "tar",
        ".tar.bz2": "tar",
        ".tar": "tar",
    }

    @staticmethod
    def _safe_target_path(target_dir: Path, member_name: str) -> Path:
        """返回成员解压目标路径，并确保不会逃逸出目标目录。"""
        dest_path = target_dir / member_name
        target_root = target_dir.resolve()
        resolved_dest = dest_path.resolve()
        try:
            resolved_dest.relative_to(target_root)
        except ValueError as exc:
            raise ValueError(f"压缩包包含不安全路径: {member_name}") from exc
        return dest_path

    @classmethod
    def get_archive_type(cls, filename: str) -> Optional[str]:
        """
        根据文件名获取压缩包类型

        Args:
            filename: 文件名

        Returns:
            压缩包类型，不支持返回 None
        """
        for ext, archive_type in cls.SUPPORTED_FORMATS.items():
            if filename.endswith(ext):
                return archive_type
        return None

    @classmethod
    def get_base_name(cls, filename: str) -> Optional[str]:
        """
        获取压缩包解压后的目录名

        Args:
            filename: 文件名

        Returns:
            基础目录名，不支持返回 None
        """
        if filename.endswith(".tar.gz"):
            return filename[:-7]
        elif filename.endswith(".tar.bz2"):
            return filename[:-8]
        elif filename.endswith(".zip"):
            return filename[:-4]
        elif filename.endswith(".tar"):
            return filename[:-4]
        return None

    @classmethod
    def is_already_extracted(cls, target_dir: Path, archive_path: Path) -> bool:
        """
        检查压缩包是否已解压

        判断依据：
        1. 目标目录存在且非空
        2. 目标目录的修改时间 >= 压缩包的修改时间（确保解压内容是最新的）

        Args:
            target_dir: 解压目标目录
            archive_path: 压缩包路径

        Returns:
            已解压返回 True，否则返回 False
        """
        if not target_dir.exists():
            return False

        if not target_dir.is_dir():
            return False

        # 检查目录是否非空
        if not any(target_dir.iterdir()):
            return False

        # 检查修改时间：目标目录应该比压缩包新或相同
        # 如果压缩包更新了，应该重新解压
        try:
            archive_mtime = archive_path.stat().st_mtime
            target_mtime = target_dir.stat().st_mtime
            if target_mtime < archive_mtime:
                # 压缩包比目标目录新，需要重新解压
                return False
        except Exception:
            pass

        return True

    def extract(
        self, archive_path: Path, output_dir: Path
    ) -> Optional[Path]:
        """
        解压压缩包

        Args:
            archive_path: 压缩包路径
            output_dir: 输出目录

        Returns:
            解压后的目录路径，失败返回 None
        """
        base_name = self.get_base_name(archive_path.name)
        if not base_name:
            Logger.warning(f"不支持的压缩格式: {archive_path.name}")
            return None

        target_dir = output_dir / base_name

        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            archive_type = self.get_archive_type(archive_path.name)
            if archive_type == "zip":
                self._extract_zip(archive_path, target_dir)
            elif archive_type == "tar":
                self._extract_tar(archive_path, target_dir)
            else:
                Logger.warning(f"不支持的压缩格式: {archive_path.name}")
                return None

            Logger.success(f"解压到: {target_dir}")
            return target_dir

        except Exception as e:
            Logger.error(f"解压失败: {e}")
            # 清理空目录
            if target_dir.is_dir() and not any(target_dir.iterdir()):
                target_dir.rmdir()
            return None

    def _extract_zip(self, archive_path: Path, target_dir: Path) -> None:
        """解压 ZIP 文件，自动展平单层顶层目录"""
        with zipfile.ZipFile(archive_path, "r") as zf:
            entries = [p for p in zf.namelist() if p]
            if not entries:
                return
            for member in entries:
                self._safe_target_path(target_dir, member)

            top_dirs = {Path(p).parts[0] for p in entries if Path(p).parts}

            if len(top_dirs) == 1:
                # 有单一顶层目录，展平
                prefix = top_dirs.pop() + "/"
                for member in entries:
                    if member.startswith(prefix):
                        # 重新映射路径
                        new_path = member[len(prefix):]
                        if new_path:
                            source = zf.read(member)
                            dest_path = self._safe_target_path(target_dir, new_path)
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(dest_path, "wb") as f:
                                f.write(source)
                    else:
                        dest_path = self._safe_target_path(target_dir, member)
                        if not member.endswith("/"):
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(dest_path, "wb") as f:
                                f.write(zf.read(member))
            else:
                for member in entries:
                    dest_path = self._safe_target_path(target_dir, member)
                    if not member.endswith("/"):
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(dest_path, "wb") as f:
                            f.write(zf.read(member))

    def _extract_tar(self, archive_path: Path, target_dir: Path) -> None:
        """解压 TAR 文件（支持 .tar.gz, .tar.bz2），自动展平单层顶层目录"""
        # 确定打开模式（字面量类型便于静态检查匹配 tarfile.open 重载）
        mode: Literal["r:gz", "r:bz2", "r"] = "r"
        if archive_path.name.endswith(".tar.gz"):
            mode = "r:gz"
        elif archive_path.name.endswith(".tar.bz2"):
            mode = "r:bz2"

        with tarfile.open(archive_path, mode) as tf:
            members = [m for m in tf.getmembers() if m.name]
            if not members:
                return
            for member in members:
                self._safe_target_path(target_dir, member.name)

            top_dirs = {Path(m.name).parts[0] for m in members}

            if len(top_dirs) == 1:
                # 有单一顶层目录，展平
                prefix = top_dirs.pop() + "/"
                for member in members:
                    if member.name.startswith(prefix):
                        # 修改成员路径，去掉顶层目录
                        member.name = member.name[len(prefix):]
                    if member.name:  # 避免空路径
                        self._extract_tar_member(tf, member, target_dir)
            else:
                for member in members:
                    self._extract_tar_member(tf, member, target_dir)

    def _extract_tar_member(
        self, tf: tarfile.TarFile, member: tarfile.TarInfo, target_dir: Path
    ) -> None:
        """安全解压单个 TAR 成员。"""
        dest_path = self._safe_target_path(target_dir, member.name)
        if member.isdir():
            dest_path.mkdir(parents=True, exist_ok=True)
            return
        if not member.isfile():
            return

        source = tf.extractfile(member)
        if source is None:
            return

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with source, open(dest_path, "wb") as f:
            shutil.copyfileobj(source, f)


class FileRenamer:
    """文件重命名器"""

    # 匹配 icp-monitoring 或 icp_monitoring 开头的文件，去除版本号等后缀
    RENAME_PATTERN = re.compile(
        r"(icp[_-]monitoring)(?:[-_]?v?\d[\d.]*(?:[-_][\w]+)*)?(.*)",
        re.IGNORECASE,
    )

    def rename_files(self, extract_dir: Path) -> List[Tuple[str, str]]:
        """
        将解压出的 icp-monitoring_* 文件重命名为 icp-monitoring*

        Args:
            extract_dir: 解压目录

        Returns:
            重命名记录列表 (旧名, 新名)
        """
        targets = self._get_targets(extract_dir)
        renamed = []

        for file_path in targets:
            new_name = self._generate_new_name(file_path.name)
            if not new_name or new_name == file_path.name:
                continue

            new_path = file_path.parent / new_name
            if new_path.exists():
                Logger.skipped_item(new_name)
                continue

            try:
                shutil.copy2(file_path, new_path)
                renamed.append((file_path.name, new_name))
            except Exception as e:
                Logger.error(f"重命名失败 {file_path.name}: {e}")

        if renamed:
            print()
            Logger.step(f"{Logger.CYAN}{Logger.ICON_RENAME}{Logger.RESET} 文件重命名")
            for old, new in renamed:
                print(f"   {old} {Logger.GRAY}→{Logger.RESET} {Logger.CYAN}{new}{Logger.RESET}")

        return renamed

    def _get_targets(self, extract_path: Path) -> List[Path]:
        """获取需要重命名的目标文件列表"""
        if extract_path.is_file():
            return [extract_path]
        elif extract_path.is_dir():
            return [f for f in extract_path.iterdir() if f.is_file()]
        return []

    def _generate_new_name(self, filename: str) -> Optional[str]:
        """生成新的文件名"""
        match = self.RENAME_PATTERN.match(filename)
        if not match:
            return None

        base = match.group(1).lower().replace("_", "-")  # icp-monitoring
        ext = match.group(2)  # 版本号/平台信息之后的残留部分，通常是扩展名
        return base + ext if ext else base


class PostProcessor:
    """后处理器：解压 + 重命名"""

    def __init__(self):
        self.extractor = ArchiveExtractor()
        self.renamer = FileRenamer()

    def process(
        self, archive_path: Path, output_dir: Path, skip_existing: bool = True
    ) -> Optional[Path]:
        """
        处理压缩包：解压并重命名

        Args:
            archive_path: 压缩包路径
            output_dir: 输出目录
            skip_existing: 是否跳过已解压的压缩包

        Returns:
            解压后的目录路径，失败返回 None
        """
        base_name = self.extractor.get_base_name(archive_path.name)
        target_dir = output_dir / base_name if base_name else None

        # 检查是否已解压
        if (
            skip_existing
            and target_dir
            and self.extractor.is_already_extracted(target_dir, archive_path)
        ):
            Logger.skipped_item(base_name, "已解压")
            # 即使跳过解压，也检查是否需要重命名
            self.renamer.rename_files(target_dir)
            return target_dir

        extract_dir = self.extractor.extract(archive_path, output_dir)

        if extract_dir:
            Logger.success_item(base_name)
            self.renamer.rename_files(extract_dir)

        return extract_dir

    def process_batch(
        self, archive_paths: List[Path], output_dir: Path, skip_existing: bool = True
    ) -> List[Path]:
        """
        批量处理压缩包

        Args:
            archive_paths: 压缩包路径列表
            output_dir: 输出目录
            skip_existing: 是否跳过已解压的压缩包

        Returns:
            成功处理的目录路径列表
        """
        processed = []
        for archive_path in archive_paths:
            if self.extractor.get_archive_type(archive_path.name):
                result = self.process(archive_path, output_dir, skip_existing)
                if result:
                    processed.append(result)
        return processed
