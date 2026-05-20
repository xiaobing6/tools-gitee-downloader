# CLAUDE.md

本文件为 SOLO 提供该项目的使用指南和代码索引。

---

## 📋 项目概览

**项目名称**: Gitee Release 自动下载工具  
**版本**: 2.0.0  
**用途**: 从 Gitee 指定仓库的 Release 记录中自动下载最新版本的安装包

---

## 📁 文件清单

### 核心文件

| 文件路径 | 说明 | 关键类/函数 |
|----------|------|-------------|
| `main.py` | 程序入口 | `parse_arguments()`, `main()` |
| `gitee_downloader/__init__.py` | 包初始化 | 版本信息 |
| `gitee_downloader/config.py` | 配置管理 | `Config` |
| `gitee_downloader/api.py` | Gitee API 封装 | `GiteeAPI`, `ReleaseManager` |
| `gitee_downloader/downloader.py` | 下载逻辑 | `FileDownloader`, `BatchDownloader`, `DownloadTask` |
| `gitee_downloader/extractor.py` | 解压和重命名 | `ArchiveExtractor`, `FileRenamer`, `PostProcessor` |
| `gitee_downloader/utils.py` | 工具函数 | `Logger`, `ProgressBar`, `format_file_size()` |

### 其他文件

| 文件 | 说明 |
|------|------|
| `CLAUDE.md` | 项目文档（本文件） |
| `gitee-downloader.yaml` | 配置文件示例 |
| `downloads/` | 默认下载目录（存放压缩包及解压后的文件） |

---

## 🚀 快速开始

### 运行程序

```bash
# 使用默认配置下载
python main.py

# 使用配置文件
python main.py --config gitee-downloader.yaml

# 生成配置文件示例
python main.py --init-config

# 下载指定文件类型
python main.py --file-filter "*.tar.gz"

# 指定版本 tag
python main.py --tag v0.9.156

# 指定下载目录
python main.py --output-dir ./packages

# 指定其他仓库
python main.py --owner other-user --repo other-repo --token YOUR_TOKEN
```

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--config` | 自动查找 | 配置文件路径 (支持 .yaml, .yml, .json) |
| `--init-config` | - | 生成默认配置文件 |
| `--owner` | `bio-sense` | 仓库所有者 |
| `--repo` | `icp-monitoring-app` | 仓库名称 |
| `--token` | 内置 token | Gitee 访问令牌 |
| `--output-dir` | `./downloads` | 下载保存目录 |
| `--file-filter` | `*` | 文件名过滤模式 |
| `--tag` | 最新版本 | 指定版本 tag |

---

## 🏗️ 架构说明

### 模块依赖关系

```
main.py
    ├── config.Config
    ├── api.GiteeAPI
    ├── api.ReleaseManager
    ├── downloader.FileDownloader
    ├── downloader.BatchDownloader
    ├── extractor.PostProcessor
    └── utils.Logger
    └── utils.ProgressBar
```

### 执行流程

```
1. main.py 解析命令行参数
    ↓
2. config.Config 加载配置（支持配置文件）
    ↓
3. api.ReleaseManager 查找目标 release
    ↓
4. downloader.BatchDownloader 批量下载（带进度条）
    ↓
5. extractor.PostProcessor 解压和重命名（检查是否已解压）
    ↓
6. 输出下载摘要
```

---

## 🔧 模块详解

### config.py - 配置管理

**Config 类**
- 属性: `base_url`, `default_token`, `default_owner`, `default_repo`, `timeout`, `file_filter`, `auto_extract`, `auto_rename` 等
- 方法:
  - `from_args(args)` - 从命令行参数创建配置
  - `from_file(path)` - 从 YAML/JSON 文件加载配置
  - `find_config_file()` - 自动查找配置文件
  - `save_to_file(path, format)` - 保存配置到文件
  - `get_token(args_token)` - 获取 token（优先级：参数 > 环境变量 > 配置文件 > 默认值）
  - `get_output_dir(args_output_dir)` - 获取输出目录

### api.py - API 封装

**GiteeAPI 类**
- 方法:
  - `get_releases(owner, repo)` - 获取 releases 列表
  - `get_release_attachments(owner, repo, release_id)` - 获取附件列表
  - `get_download_url(owner, repo, release_id, attach_file_id)` - 获取下载 URL

**ReleaseManager 类**
- 方法:
  - `find_release(owner, repo, tag)` - 查找目标 release
  - `get_attachments(owner, repo, release_id, pattern)` - 获取并过滤附件

### downloader.py - 下载器

**FileDownloader 类**
- 方法:
  - `download(download_url, save_path, skip_existing)` - 下载单个文件（带进度条）

**BatchDownloader 类**
- 方法:
  - `add_task(name, url, save_path)` - 添加下载任务
  - `download_all()` - 执行所有下载任务
  - `get_summary()` - 获取下载摘要

**DownloadTask 类**
- 属性: `name`, `url`, `save_path`, `success`, `skipped`

### extractor.py - 解压处理

**ArchiveExtractor 类**
- 支持格式: `.zip`, `.tar.gz`, `.tar.bz2`, `.tar`
- 方法:
  - `extract(archive_path, output_dir, skip_existing=True)` - 解压压缩包
  - `is_already_extracted(target_dir, archive_path)` - 检查是否已解压
  - 自动展平单层顶层目录

**FileRenamer 类**
- 功能: 将 `icp-monitoring-v0.9.xxx` 重命名为 `icp-monitoring`
- 方法:
  - `rename_files(extract_dir)` - 重命名文件

**PostProcessor 类**
- 方法:
  - `process(archive_path, output_dir, skip_existing=True)` - 解压并重命名
  - `process_batch(archive_paths, output_dir, skip_existing=True)` - 批量处理

### utils.py - 工具函数

**Logger 类**
- 静态方法: `info()`, `warning()`, `error()`, `success()`, `skip()`

**ProgressBar 类**
- 功能: 终端下载进度条，显示百分比、速度、已用时间
- 方法:
  - `update(chunk_size)` - 更新已下载字节数
  - `finish()` - 下载完成，打印最终状态
- 显示格式: `filename  [████████░░░░] 66.7%  15.2MB/22.8MB  2.1MB/s  7.2s`

**工具函数**
- `setup_windows_encoding()` - 修复 Windows 中文乱码
- `is_already_downloaded(save_path)` - 检查文件是否已下载
- `format_file_size(size_bytes)` - 格式化文件大小

---

## 📝 开发笔记

### 代码风格
- 使用类型注解（Type Hints）
- 使用 dataclass 管理配置
- 使用面向对象设计
- 详细的 docstring 文档

### 待优化项
- [x] 添加下载进度条
- [x] 添加配置文件支持（YAML/JSON）
- [x] 解压时检查是否已解压，避免重复解压

> **说明**:
> - 并发下载对于本项目（单文件、小体积）不适用，已从列表中移除。
> - 单元测试对于个人工具维护成本较高，暂不考虑。

---

## 📝 更新记录

| 日期 | 变更内容 |
|------|----------|
| 2026-05-13 | 同步 CLAUDE.md 与项目最新状态 |
| 2026-05-12 | 新增解压检查功能，避免重复解压 |
| 2026-05-12 | 新增配置文件支持（YAML/JSON） |
| 2026-05-12 | 新增 `ProgressBar` 进度条功能 |
| 2026-05-12 | 初始创建项目文档 |

---

## 🔗 相关链接

- Gitee API v5 文档: https://gitee.com/api/v5/swagger

---

*文档生成时间: 2026-05-12*  
*最后更新: 2026-05-13*  
*生成工具: SOLO*
