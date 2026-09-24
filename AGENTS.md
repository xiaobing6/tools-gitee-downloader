# AGENTS.md

本文件为 Codex 等代码代理提供项目维护约定和代码索引。用户使用说明请看 `README.md`。

## 项目概况

- 项目名称：Gitee Release 自动下载工具。
- 当前版本：`2.0.0`，见 `src/gitee_downloader/__init__.py`。
- 用途：从 Gitee 指定仓库的 Release 记录中下载附件，并按需解压、重命名。
- 依赖管理使用 `uv`：运行依赖在 `pyproject.toml` 的 `dependencies`（`requests`、`pyyaml`），锁定在 `uv.lock`，环境由 `uv sync` 创建。
- 开发依赖分组 `[dependency-groups] dev` 现有 `pytest`、`ruff`、`mypy`。除这三者外不引入 `click`、`typer`、`rich` 等额外工程依赖，除非用户明确要求。

## 文件索引

| 文件/目录 | 说明 |
|-----------|------|
| `pyproject.toml` | 项目元数据、依赖、dev 分组、console script 和 ruff 配置 |
| `.python-version` | 固定 Python 3.12 |
| `uv.lock` | uv 锁定文件，应提交 |
| `src/gitee_downloader/__main__.py` | CLI 入口和主流程编排 |
| `src/gitee_downloader/config.py` | 配置加载、保存、token 优先级 |
| `src/gitee_downloader/api.py` | Gitee API 封装和 release 查找 |
| `src/gitee_downloader/downloader.py` | 文件下载、`.part` 临时文件、批量统计 |
| `src/gitee_downloader/extractor.py` | 安全解压和重命名 |
| `src/gitee_downloader/utils.py` | 日志、进度条、编码和格式化工具 |
| `tests/` | 纯逻辑单元测试，禁止网络请求 |
| `gitee-downloader.example.yaml` | 可提交的配置示例 |
| `gitee-downloader.yaml` | 本地私有配置，已忽略，不应提交 |
| `.editorconfig` | 编辑器基础约束 |
| `.gitattributes` | Git 换行规范 |
| `.github/workflows/auto-pr.yml` | 非 main 分支 push 后自动创建 PR |

## 执行流程

```text
src/gitee_downloader/__main__.py
  -> Config 加载命令行参数或本地配置
  -> ReleaseManager 查找指定 tag 或最新 release
  -> ReleaseManager 获取并按 file_filter 过滤附件
  -> BatchDownloader 下载附件，已存在文件会做大小校验
  -> PostProcessor 安全解压并执行重命名
  -> 输出处理摘要和下载目录
```

入口方式：`uv run gitee-downloader` 或 `uv run python -m gitee_downloader`。

## 关键约定

- 真实 token 不得写入代码、文档或可提交文件。`gitee-downloader.yaml` 是本地私有配置（已被 `.gitignore` 忽略）；`gitee-downloader.example.yaml` 只使用 `YOUR_GITEE_TOKEN` 占位符，且 `Config.get_token()` 必须把占位符当作未配置处理。
- token 优先级：命令行参数 > 环境变量 `GITEE_TOKEN` > 配置文件 > 空字符串（已有测试锁定，改动时同步测试）。
- 配置只支持 YAML；重命名由 `PostProcessor` 无条件执行，没有配置开关。
- 新增解压格式时必须保留路径安全校验，不能直接使用 `extractall()`。
- 修改终端输出时需考虑 Windows Terminal、PowerShell、GBK 控制台和 emoji 兼容，降级处理参考 `Logger._print` 和 `ProgressBar`。
- `tests/` 只写纯逻辑测试，不得发起网络请求。
- 本地产物（`downloads/`、`dist/`、`*.part` 等）不提交，忽略规则见 `.gitignore`。

## 常用检查

```powershell
uv sync
uv run pytest -q
uv run ruff check .
uv run mypy src tests
uv run gitee-downloader --help
git status -sb --ignored
git check-ignore -v gitee-downloader.yaml
```
