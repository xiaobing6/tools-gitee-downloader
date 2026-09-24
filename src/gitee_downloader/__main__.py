#!/usr/bin/env python3
"""
Gitee Release 自动下载工具

从 Gitee 指定仓库的 Release 记录中下载最新版本的安装包

支持配置文件：gitee-downloader.yaml / gitee-downloader.yml
"""

import argparse
import sys
from pathlib import Path

from gitee_downloader import __version__
from gitee_downloader.config import Config
from gitee_downloader.api import GiteeAPI, ReleaseManager
from gitee_downloader.downloader import FileDownloader, BatchDownloader
from gitee_downloader.extractor import PostProcessor
from gitee_downloader.utils import setup_windows_encoding, Logger


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        prog="gitee-downloader",
        description="从 Gitee 仓库 Release 下载最新版本安装包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 首次使用：生成本地配置文件
  gitee-downloader --init-config

  # 查看版本
  gitee-downloader --version

  # 编辑 gitee-downloader.yaml，将 YOUR_GITEE_TOKEN 替换为真实 token 后运行
  gitee-downloader

  # 使用配置文件
  gitee-downloader --config gitee-downloader.yaml

  # 下载指定文件类型
  gitee-downloader --file-filter "*.tar.gz"

  # 指定版本 tag
  gitee-downloader --tag v0.9.156

  # 指定下载目录
  gitee-downloader --output-dir ./packages

  # 指定其他仓库
  gitee-downloader --owner other-user --repo other-repo --token YOUR_GITEE_TOKEN
        """,
    )

    parser.add_argument(
        "--config",
        default=None,
        help="配置文件路径 (支持 .yaml, .yml)",
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="生成本地配置文件 (gitee-downloader.yaml) 并退出",
    )
    parser.add_argument(
        "--owner",
        default=None,
        help="仓库所有者 (默认: bio-sense，优先级: 命令行 > 配置文件 > 内置)",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="仓库名称 (默认: icp-monitoring-app，优先级: 命令行 > 配置文件 > 内置)",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Gitee 访问令牌（优先级: 命令行 > 环境变量 GITEE_TOKEN > 配置文件 > 未配置）",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="下载保存目录 (默认: ./downloads，优先级: 命令行 > 配置文件 > 内置)",
    )
    parser.add_argument(
        "--file-filter",
        default=None,
        help="文件名过滤模式，如 *.tar.gz (默认: *)",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="指定版本 tag（不指定则取最新）",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser.parse_args()


def init_config_file() -> None:
    """生成默认配置文件"""
    config_path = Path("gitee-downloader.yaml")

    if config_path.exists():
        Logger.warning(f"配置文件已存在: {config_path}")
        response = input("是否覆盖? (y/N): ")
        if response.lower() != "y":
            Logger.info("已取消")
            return

    config = Config()
    config.save_to_file(config_path, format="yaml")
    Logger.success(f"配置文件已生成: {config_path.resolve()}")
    Logger.info("请将 token: YOUR_GITEE_TOKEN 替换为真实 Gitee token")
    Logger.info("您可以继续编辑此文件来自定义其他配置")


def load_config(args) -> Config:
    """
    加载配置，优先级：
    1. 命令行参数 --config 指定的配置文件
    2. 自动查找默认配置文件
    3. 内置非敏感默认值
    """
    # 1. 如果指定了 --config，使用指定文件
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            Logger.error(f"配置文件不存在: {config_path}")
            sys.exit(1)
        Logger.step(f"加载配置文件: {config_path}")
        return Config.from_file(config_path)

    # 2. 自动查找默认配置文件
    auto_config = Config.find_config_file()
    if auto_config:
        Logger.info(str(auto_config), Logger.ICON_CONFIG)
        return Config.from_file(auto_config)

    # 3. 使用内置默认值
    return Config()


def merge_config_with_args(config: Config, args) -> Config:
    """
    命令行参数覆盖配置文件中的值
    优先级：命令行参数 > 配置文件 > 内置非敏感默认值
    """
    if args.owner:
        config.default_owner = args.owner
    if args.repo:
        config.default_repo = args.repo
    if args.output_dir:
        config.default_output_dir = args.output_dir
    if args.file_filter:
        config.file_filter = args.file_filter

    return config


def main() -> int:
    """主函数"""
    # 修复 Windows 中文乱码
    setup_windows_encoding()

    # 解析参数
    args = parse_arguments()

    # 生成配置文件示例
    if args.init_config:
        init_config_file()
        return 0
    # 加载配置
    config = load_config(args)
    config = merge_config_with_args(config, args)

    token = config.get_token(args.token)
    output_dir = config.get_output_dir(args.output_dir)

    # 初始化组件
    api = GiteeAPI(config, token)
    release_manager = ReleaseManager(api)

    # ═══════════════════════════════════════════════════════════
    # 阶段 1：查找 Release
    # ═══════════════════════════════════════════════════════════
    Logger.inline_status(
        Logger.ICON_FETCH,
        f"{Logger.CYAN}{config.default_owner}/{config.default_repo}{Logger.RESET}",
        end="",
    )

    target_release = release_manager.find_release(
        config.default_owner, config.default_repo, args.tag
    )

    if not target_release:
        print()  # 换行
        Logger.error("无法获取 release 信息，请检查仓库地址、tag 和 token")
        return 1

    release_id = target_release.get("id")
    if release_id is None:
        Logger.error("release 信息中缺少 id，无法继续")
        return 1
    tag_name = target_release.get("tag_name", "unknown")
    print()
    print(
        f"   {Logger.GREEN}{Logger.ICON_SUCCESS}{Logger.RESET} "
        f"{Logger.CYAN}{tag_name}{Logger.RESET} {Logger.GRAY}(ID: {release_id}){Logger.RESET}"
    )

    # ═══════════════════════════════════════════════════════════
    # 阶段 2：获取附件列表
    # ═══════════════════════════════════════════════════════════
    attachments = release_manager.get_attachments(
        config.default_owner, config.default_repo, release_id, config.file_filter
    )

    if not attachments:
        print()
        if config.file_filter != "*":
            Logger.warning(f"没有匹配 '{config.file_filter}' 的附件")
        else:
            Logger.warning("该 release 没有附件")
        return 0

    print(
        f"   {Logger.GREEN}{Logger.ICON_SUCCESS}{Logger.RESET} "
        f"{Logger.CYAN}{len(attachments)}{Logger.RESET} 个文件待下载"
    )

    # 准备下载任务
    downloader = FileDownloader(config, token)
    batch_downloader = BatchDownloader(downloader)

    for att in attachments:
        name = att.get("name", "unknown")
        att_id = att.get("id")
        if att_id is None:
            Logger.warning(f"附件 {name} 缺少 id，跳过")
            continue
        download_url = api.get_download_url(
            config.default_owner, config.default_repo, release_id, att_id
        )
        save_path = output_dir / name
        batch_downloader.add_task(name, download_url, save_path)

    # ═══════════════════════════════════════════════════════════
    # 阶段 3：下载文件
    # ═══════════════════════════════════════════════════════════
    downloaded_files = batch_downloader.download_all()

    # ═══════════════════════════════════════════════════════════
    # 阶段 4：解压和重命名
    # ═══════════════════════════════════════════════════════════
    if config.auto_extract:
        post_processor = PostProcessor()
        post_processor.process_batch(downloaded_files, output_dir)

    # ═══════════════════════════════════════════════════════════
    # 完成摘要
    # ═══════════════════════════════════════════════════════════
    summary = batch_downloader.get_summary()
    handled = summary["success"] + summary["skipped"]
    print()
    print(
        f"{Logger.GREEN}{Logger.ICON_SUCCESS}{Logger.RESET} "
        f"处理完成: {Logger.CYAN}{handled}/{summary['total']}{Logger.RESET}"
    )
    if summary["success"] > 0:
        Logger.success(f"下载 {summary['success']} 个")
    if summary["skipped"] > 0:
        Logger.skip(f"跳过 {summary['skipped']} 个")
    if summary["failed"] > 0:
        Logger.error(f"失败 {summary['failed']} 个")
    print()
    Logger.path(f"{output_dir.resolve()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
