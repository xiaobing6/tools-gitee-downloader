"""下载器模块"""

from pathlib import Path
from typing import List

import requests

from .config import Config
from .utils import Logger, ProgressBar, format_file_size, is_already_downloaded


class FileDownloader:
    """文件下载器"""

    def __init__(self, config: Config, token: str):
        self.config = config
        self.token = token

    def _headers(self) -> dict:
        """生成请求头"""
        return {"PRIVATE-TOKEN": self.token} if self.token else {}

    def download(
        self, download_url: str, save_path: Path, skip_existing: bool = True
    ) -> bool:
        """
        下载文件到指定路径（带进度条）

        Args:
            download_url: 下载 URL
            save_path: 保存路径
            skip_existing: 是否跳过已存在的文件

        Returns:
            下载成功返回 True
        """
        if skip_existing and is_already_downloaded(save_path):
            Logger.skipped_item(save_path.name)
            return True

        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            resp = requests.get(
                download_url,
                headers=self._headers(),
                stream=True,
                timeout=self.config.download_timeout,
            )
            resp.raise_for_status()

            # 获取文件总大小
            total_size = int(resp.headers.get("content-length", 0))

            # 初始化进度条
            progress = ProgressBar(save_path.name, total_size)

            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=self.config.chunk_size):
                    if chunk:
                        f.write(chunk)
                        progress.update(len(chunk))

            progress.finish()

            size = save_path.stat().st_size
            Logger.success_item(save_path.name, format_file_size(size))
            return True

        except requests.exceptions.RequestException as e:
            Logger.error(f"下载文件失败: {e}")
            return False


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
            already_downloaded = is_already_downloaded(task.save_path)
            if self.downloader.download(task.url, task.save_path, skip_existing=True):
                if already_downloaded:
                    task.skipped = True
                else:
                    task.success = True
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
