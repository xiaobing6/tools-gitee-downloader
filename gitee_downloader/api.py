"""Gitee API 封装模块"""

from typing import Dict, List, Optional, Any

import requests

from .config import Config
from .utils import Logger


class GiteeAPI:
    """Gitee API 客户端"""

    def __init__(self, config: Config, token: str):
        self.config = config
        self.token = token
        self.base_url = config.base_url

    def _headers(self) -> Dict[str, str]:
        """生成 API 请求头"""
        return {"PRIVATE-TOKEN": self.token} if self.token else {}

    def get_releases(self, owner: str, repo: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取仓库的 releases 列表，按创建时间倒序（最新在前）

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            releases 列表，失败返回 None
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/releases"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self.config.timeout)
            resp.raise_for_status()
            releases = resp.json()
            # 按创建时间倒序排序，确保第一个是最新的
            releases.sort(key=lambda r: r.get("created_at", ""), reverse=True)
            return releases
        except requests.exceptions.RequestException as e:
            Logger.error(f"获取 releases 失败: {e}")
            return None

    def get_release_attachments(
        self, owner: str, repo: str, release_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取指定 release 的附件列表

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            release_id: release ID

        Returns:
            附件列表，失败返回 None
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/releases/{release_id}/attach_files"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self.config.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            Logger.error(f"获取附件列表失败: {e}")
            return None

    def get_download_url(
        self, owner: str, repo: str, release_id: int, attach_file_id: int
    ) -> str:
        """
        获取附件下载 URL

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            release_id: release ID
            attach_file_id: 附件文件 ID

        Returns:
            下载 URL
        """
        return (
            f"{self.base_url}/repos/{owner}/{repo}"
            f"/releases/{release_id}/attach_files/{attach_file_id}/download"
        )


class ReleaseManager:
    """Release 管理器"""

    def __init__(self, api: GiteeAPI):
        self.api = api

    def find_release(
        self, owner: str, repo: str, tag: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        查找目标 release

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            tag: 指定版本 tag，不指定则返回最新的

        Returns:
            release 信息，未找到返回 None
        """
        releases = self.api.get_releases(owner, repo)
        if not releases:
            return None

        if tag:
            for release in releases:
                if release.get("tag_name") == tag:
                    return release
            Logger.warning(f"未找到 tag 为 '{tag}' 的 release")
            return None

        return releases[0]  # 第一个为最新

    def get_attachments(
        self, owner: str, repo: str, release_id: int, pattern: str = "*"
    ) -> List[Dict[str, Any]]:
        """
        获取并过滤附件

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            release_id: release ID
            pattern: 文件名过滤模式

        Returns:
            过滤后的附件列表
        """
        import fnmatch

        attachments = self.api.get_release_attachments(owner, repo, release_id)
        if attachments is None:
            return []

        if pattern == "*":
            return attachments

        return [a for a in attachments if fnmatch.fnmatch(a.get("name", ""), pattern)]
