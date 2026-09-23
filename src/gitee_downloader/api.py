"""Gitee API 封装模块"""

import fnmatch
from typing import Dict, List, Optional, Any
from urllib.parse import quote

import requests

from .config import Config
from .utils import Logger, build_headers


class GiteeAPI:
    """Gitee API 客户端"""

    def __init__(self, config: Config, token: str):
        self.config = config
        self.token = token
        self.base_url = config.base_url

    def get_latest_release(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        获取仓库最后更新的 release。

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            release 信息，失败返回 None
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/releases/latest"
        try:
            resp = requests.get(url, headers=build_headers(self.token), timeout=self.config.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            Logger.error(f"获取最新 release 失败: {e}")
            return None

    def get_release_by_tag(
        self, owner: str, repo: str, tag: str
    ) -> Optional[Dict[str, Any]]:
        """
        根据 tag 获取仓库 release。

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            tag: release tag

        Returns:
            release 信息，失败返回 None
        """
        encoded_tag = quote(tag, safe="")
        url = f"{self.base_url}/repos/{owner}/{repo}/releases/tags/{encoded_tag}"
        try:
            resp = requests.get(url, headers=build_headers(self.token), timeout=self.config.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                Logger.warning(f"未找到 tag 为 '{tag}' 的 release")
            else:
                Logger.error(f"获取 tag release 失败: {e}")
            return None
        except requests.exceptions.RequestException as e:
            Logger.error(f"获取 tag release 失败: {e}")
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
            resp = requests.get(url, headers=build_headers(self.token), timeout=self.config.timeout)
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
        if tag:
            return self.api.get_release_by_tag(owner, repo, tag)

        return self.api.get_latest_release(owner, repo)

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
        attachments = self.api.get_release_attachments(owner, repo, release_id)
        if attachments is None:
            return []

        if pattern == "*":
            return attachments

        return [a for a in attachments if fnmatch.fnmatch(a.get("name", ""), pattern)]
