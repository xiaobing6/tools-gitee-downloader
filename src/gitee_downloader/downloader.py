"""下载器模块"""

from pathlib import Path
from typing import List, Literal, Optional

import requests

from .config import Config
from .utils import Logger, ProgressBar, build_headers, format_file_size, is_already_downloaded

DownloadStatus = Literal["downloaded", "skipped", "failed"]


class FileDownloader:
    """文件下载器"""

    def __init__(self, config: Config, token: str):
        self.config = config
        self.token = token

    def _remote_size(self, download_url: str) -> Optional[int]:
        """Return remote content length when the server exposes it."""
        try:
            resp = requests.head(
                download_url,
                headers=build_headers(self.token),
                allow_redirects=True,
                timeout=self.config.timeout,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException:
            return None

        content_length = resp.headers.get("content-length")
        if not content_length:
            return None

        try:
            return int(content_length)
        except ValueError:
            return None

    def _should_skip_existing(self, download_url: str, save_path: Path) -> bool:
        """Decide whether an existing local file can be trusted."""
        if not is_already_downloaded(save_path):
            return False

        local_size = save_path.stat().st_size
        remote_size = self._remote_size(download_url)
        if remote_size is None or local_size == remote_size:
            Logger.skipped_item(save_path.name)
            return True

        Logger.warning(
            f"{save_path.name} 本地大小 {format_file_size(local_size)} "
            f"与远端大小 {format_file_size(remote_size)} 不一致，重新下载"
        )
        return False

    def download(
        self, download_url: str, save_path: Path, skip_existing: bool = True
    ) -> DownloadStatus:
        """
        下载文件到指定路径（带进度条）

        Args:
            download_url: 下载 URL
            save_path: 保存路径
            skip_existing: 是否跳过已存在的文件

        Returns:
            返回 downloaded/skipped/failed
        """
        if skip_existing and self._should_skip_existing(download_url, save_path):
            return "skipped"

        temp_path = save_path.with_name(f"{save_path.name}.part")
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            if temp_path.exists():
                temp_path.unlink()

            resp = requests.get(
                download_url,
                headers=build_headers(self.token),
                stream=True,
                timeout=self.config.download_timeout,
            )
            resp.raise_for_status()

            # 获取文件总大小
            total_size = int(resp.headers.get("content-length", 0))

            # 初始化进度条
            progress = ProgressBar(save_path.name, total_size)

            with open(temp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=self.config.chunk_size):
                    if chunk:
                        f.write(chunk)
                        progress.update(len(chunk))

            progress.finish()

            temp_size = temp_path.stat().st_size
            if total_size > 0 and temp_size != total_size:
                raise IOError(
                    f"下载大小不完整: {format_file_size(temp_size)} / "
                    f"{format_file_size(total_size)}"
                )

            temp_path.replace(save_path)
            size = save_path.stat().st_size
            Logger.success_item(save_path.name, format_file_size(size))
            return "downloaded"

        except (requests.exceptions.RequestException, OSError) as e:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            Logger.error(f"下载文件失败: {e}")
            return "failed"


class DownloadTask:
    """下载任务"""

    def __init__(self, name: str, url: str, save_path: Path):
        self.name = name
        self.url = url
        self.save_path = save_path
        self.success = False
        self.skipped = False


class BatchDownloader:
    """批量下载器"""

    def __init__(self, downloader: FileDownloader):
        self.downloader = downloader
        self.tasks: List[DownloadTask] = []

    def add_task(self, name: str, url: str, save_path: Path) -> None:
        """添加下载任务"""
        self.tasks.append(DownloadTask(name, url, save_path))

    def download_all(self) -> List[Path]:
        """
        执行所有下载任务

        Returns:
            成功下载的文件路径列表
        """
        downloaded_files: List[Path] = []

        for task in self.tasks:
            status = self.downloader.download(task.url, task.save_path, skip_existing=True)
            if status == "downloaded":
                task.success = True
                downloaded_files.append(task.save_path)
            elif status == "skipped":
                task.skipped = True
                downloaded_files.append(task.save_path)
            else:
                print()  # 失败后换行

        return downloaded_files

    def get_summary(self) -> dict:
        """获取下载摘要"""
        success = sum(1 for t in self.tasks if t.success)
        skipped = sum(1 for t in self.tasks if t.skipped)
        failed = len(self.tasks) - success - skipped
        return {
            "total": len(self.tasks),
            "success": success,
            "skipped": skipped,
            "failed": failed,
        }
