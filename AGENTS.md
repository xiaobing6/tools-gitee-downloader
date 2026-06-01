# AGENTS.md

本文件为 Codex 等代码代理提供项目维护约定和代码索引。用户使用说明请看 `README.md`。

## 项目概况

- 项目名称：Gitee Release 自动下载工具。
- 当前版本：`2.0.0`，见 `gitee_downloader/__init__.py`。
- 用途：从 Gitee 指定仓库的 Release 记录中下载附件，并按需解压、重命名。
- 运行依赖只放在 `requirements.txt`：`requests`、`PyYAML`。
- 构建依赖只放在 `requirements-build.txt`，用于 Nuitka 打包 Windows exe。
- 不引入 `click`、`typer`、`rich`、`mypy` 等额外工程依赖，除非用户明确要求。

## 文件索引

| 文件/目录 | 说明 |
|-----------|------|
| `main.py` | CLI 入口和主流程编排 |
| `gitee_downloader/config.py` | 配置加载、保存、token 优先级 |
| `gitee_downloader/api.py` | Gitee API 封装和 release 查找 |
| `gitee_downloader/downloader.py` | 文件下载、`.part` 临时文件、批量统计 |
| `gitee_downloader/extractor.py` | 安全解压和重命名 |
| `gitee_downloader/utils.py` | 日志、进度条、编码和格式化工具 |
| `gitee-downloader.example.yaml` | 可提交的配置示例 |
| `gitee-downloader.yaml` | 本地私有配置，已忽略，不应提交 |
| `build.bat` | Windows Nuitka 单文件 exe 构建入口 |
| `.editorconfig` | 编辑器基础约束 |
| `.gitattributes` | Git 换行规范 |
| `.github/workflows/auto-pr.yml` | 非 main 分支 push 后自动创建 PR |

## 执行流程

```text
main.py
  -> Config 加载命令行参数或本地配置
  -> ReleaseManager 查找指定 tag 或最新 release
  -> ReleaseManager 获取并按 file_filter 过滤附件
  -> BatchDownloader 下载附件，已存在文件会做大小校验
  -> PostProcessor 安全解压并执行重命名
  -> 输出处理摘要和下载目录
```

## 关键约定

- 真实 token 不应写入代码、文档或可提交配置。
- `gitee-downloader.yaml` 是本地私有配置文件，必须保持 Git 忽略。
- `gitee-downloader.example.yaml` 是可提交示例，只能使用 `YOUR_GITEE_TOKEN` 占位符。
- `Config.get_token()` 必须把 `YOUR_GITEE_TOKEN` 当作未配置处理。
- Nuitka 打包命令不要加入 `--include-data-file=gitee-downloader.yaml=...`，避免把本地 token 配置打进 exe。
- `downloads/`、`dist/`、`.uploads/`、`__pycache__/`、`*.part` 都是本地产物，不应提交。
- 文本文件默认使用 UTF-8 + LF；`*.bat` 使用 CRLF。
- 新增解压格式时必须保留路径安全校验，不能直接使用 `extractall()`。
- 修改终端输出时，需要考虑 Windows Terminal、PowerShell、GBK 控制台和 emoji 兼容。

## 常用检查

```powershell
python -m compileall -q main.py gitee_downloader
python main.py --help
git status -sb --ignored
git check-ignore -v gitee-downloader.yaml
```

## 打包检查

正式分发 exe 建议使用 Python 3.13。Python 3.14 当前可能触发 Nuitka 实验性支持提示。

```powershell
.\build.bat
.\dist\gitee-downloader.exe --help
```

