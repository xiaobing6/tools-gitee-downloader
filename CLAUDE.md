# CLAUDE.md

本文件为 SOLO / Claude / Codex 提供该项目的使用指南和代码索引。

---

## 项目概览

**项目名称**: Gitee Release 自动下载工具  
**版本**: 2.0.0  
**用途**: 从 Gitee 指定仓库的 Release 记录中下载附件，并按需解压、重命名。

---

## 文件清单

### 核心代码

| 文件路径 | 说明 | 关键类/函数 |
|----------|------|-------------|
| `main.py` | CLI 入口和主流程编排 | `parse_arguments()`, `load_config()`, `main()` |
| `gitee_downloader/__init__.py` | 包初始化 | `__version__` |
| `gitee_downloader/config.py` | 配置管理 | `Config` |
| `gitee_downloader/api.py` | Gitee API 封装 | `GiteeAPI`, `ReleaseManager` |
| `gitee_downloader/downloader.py` | 下载逻辑和批量状态 | `FileDownloader`, `BatchDownloader`, `DownloadTask` |
| `gitee_downloader/extractor.py` | 安全解压和重命名 | `ArchiveExtractor`, `FileRenamer`, `PostProcessor` |
| `gitee_downloader/utils.py` | 日志、进度条、格式化工具 | `Logger`, `ProgressBar`, `setup_windows_encoding()` |

### 项目文件

| 文件/目录 | 说明 |
|-----------|------|
| `README.md` | 面向用户的使用说明 |
| `CLAUDE.md` | 项目文档和维护索引 |
| `gitee-downloader.yaml` | 本地配置文件 |
| `.gitignore` | 忽略 Python 缓存、下载产物、上传临时目录等 |
| `downloads/` | 默认下载目录，运行产物，已忽略 |
| `.uploads/` | 本地上传/临时目录，已忽略 |
| `__pycache__/` | Python 编译缓存，已忽略 |

---

## 快速开始

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
python main.py --tag v0.9.164

# 指定下载目录
python main.py --output-dir ./packages

# 指定其他仓库
python main.py --owner other-user --repo other-repo --token YOUR_TOKEN
```

---

## 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--config` | 自动查找 | 配置文件路径，支持 `.yaml`, `.yml`, `.json` |
| `--init-config` | - | 生成默认配置文件 |
| `--owner` | `bio-sense` | 仓库所有者 |
| `--repo` | `icp-monitoring-app` | 仓库名称 |
| `--token` | 内置 token | Gitee 访问令牌 |
| `--output-dir` | `./downloads` | 下载保存目录 |
| `--file-filter` | `*` | 文件名过滤模式 |
| `--tag` | 最新版本 | 指定版本 tag |

Token 获取优先级：

```text
命令行 --token > 环境变量 GITEE_TOKEN > 配置文件 token > 内置默认值
```

---

## 架构说明

### 模块依赖

```text
main.py
    ├── config.Config
    ├── api.GiteeAPI
    ├── api.ReleaseManager
    ├── downloader.FileDownloader
    ├── downloader.BatchDownloader
    ├── extractor.PostProcessor
    └── utils.Logger / utils.ProgressBar
```

### 执行流程

```text
1. main.py 初始化 Windows 输出编码并解析命令行参数
    ↓
2. config.Config 加载配置文件或命令行配置
    ↓
3. api.ReleaseManager 查找指定 tag 或最新 release
    ↓
4. api.ReleaseManager 获取并过滤附件
    ↓
5. downloader.BatchDownloader 批量下载，已存在文件会跳过
    ↓
6. extractor.PostProcessor 安全解压并执行重命名
    ↓
7. 输出处理摘要和下载目录
```

---

## 模块详解

### config.py

- `Config.from_args(args)`: 从命令行参数创建配置。
- `Config.from_file(path)`: 从 YAML/JSON 配置文件加载。
- `Config.find_config_file()`: 自动查找默认配置文件。
- `Config.save_to_file(path, format)`: 保存配置文件。
- `Config.get_token(args_token)`: 按优先级获取 token。
- `Config.get_output_dir(args_output_dir)`: 获取并创建输出目录。

### api.py

- `GiteeAPI.get_latest_release(owner, repo)`: 通过 Gitee latest 接口获取最新 release。
- `GiteeAPI.get_release_by_tag(owner, repo, tag)`: 通过 Gitee tag 接口获取指定 release。
- `GiteeAPI.get_release_attachments(owner, repo, release_id)`: 获取附件列表。
- `GiteeAPI.get_download_url(...)`: 生成附件下载 URL。
- `ReleaseManager.find_release(owner, repo, tag)`: 查找指定 tag 或最新 release。
- `ReleaseManager.get_attachments(...)`: 获取附件并按 `file_filter` 过滤。

### downloader.py

- `FileDownloader.download(...)`: 下载单个文件，负责已存在文件的跳过判断和进度条显示。
- `BatchDownloader.download_all()`: 执行所有下载任务并记录 success/skipped 状态。
- `BatchDownloader.get_summary()`: 返回 total/success/skipped/failed 摘要。

### extractor.py

- 支持 `.zip`, `.tar.gz`, `.tar.bz2`, `.tar`。
- `ArchiveExtractor.extract(...)`: 解压压缩包，自动展平单层顶层目录。
- 解压前会校验成员路径，避免 `../` 或绝对路径写出目标目录。
- 不使用 `extractall()` 或直接 `extract()`。
- `FileRenamer.rename_files(...)`: 将 `icp-monitoring_v0.9.xxx` 一类文件复制为稳定名称 `icp-monitoring`。
- `PostProcessor.process_batch(...)`: 批量处理下载成功或已存在的压缩包。

### utils.py

- `setup_windows_encoding()`: Windows 下将 stdout/stderr 配置为 UTF-8，并使用 replacement 处理不可编码字符。
- `Logger`: 统一日志输出，含安全打印降级，避免未初始化 UTF-8 时 emoji/中文导致输出异常。
- `ProgressBar`: 终端进度条，按窗口宽度自适应，中文宽字符按 East Asian Width 计算。
- 进度条状态使用分隔符展示：

```text
filename [████████░░░░] 100% | 2.3 MB | 634.0 KB/s | 3.6s
```

---

## 输出行为

- 已下载文件会显示为跳过，不重复下载。
- 已解压目录会显示为跳过，但仍会检查是否需要补充稳定文件名。
- 最终摘要使用“处理完成”，避免重复下载时出现 `下载完成: 0/1` 的误解。

示例：

```text
处理完成: 1/1
下载 1 个
跳过 1 个
失败 1 个
```

---

## 开发检查

常用检查命令：

```bash
python -m compileall -q main.py gitee_downloader
python main.py --help
```

Git 忽略规则应覆盖：

```text
downloads/
.uploads/
__pycache__/
```

---

## 维护注意

- 除非用户明确要求，不要修改 `gitee-downloader.yaml` 中的 token 策略。
- 新增解压格式时必须保留路径安全校验。
- 修改终端输出时，需要考虑 Windows Terminal、PowerShell、GBK 控制台和 emoji 兼容。
- 下载产物和缓存目录不应进入版本库。

---

## 更新记录

| 日期 | 变更内容 |
|------|----------|
| 2026-05-21 | 同步 README 和 CLAUDE 项目说明 |
| 2026-05-21 | 增强 Windows 输出兼容、进度条可读性和中文宽度计算 |
| 2026-05-21 | 收敛 Logger 输出和重复下载摘要 |
| 2026-05-21 | 增加安全解压路径校验，移除直接 `extractall()` 使用 |
| 2026-05-21 | `.gitignore` 增加 `.uploads/` |
| 2026-05-13 | 同步 CLAUDE.md 与项目状态 |
| 2026-05-12 | 新增解压检查功能，避免重复解压 |
| 2026-05-12 | 新增配置文件支持（YAML/JSON） |
| 2026-05-12 | 新增 `ProgressBar` 进度条功能 |
| 2026-05-12 | 初始创建项目文档 |

---

## 相关链接

- Gitee API v5 文档: https://gitee.com/api/v5/swagger

---

*最后更新: 2026-05-21*
