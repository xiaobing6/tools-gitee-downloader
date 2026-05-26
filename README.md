# tools-gitee-downloader

从 Gitee 仓库 Release 中下载附件，并按需解压、重命名。

## 功能

- 自动读取最新 Release，或通过 `--tag` 指定版本。
- 支持按文件名模式过滤附件，例如 `*.tar.gz`。
- 支持 YAML/JSON 配置文件。
- 下载时显示进度、大小、速度和耗时。
- 自动跳过已下载文件和已解压目录。
- 安全解压 ZIP/TAR，避免压缩包路径逃逸目标目录。
- Windows 终端下处理中文、颜色和进度条显示兼容。

## 使用

首次使用建议先生成本地配置文件，并填写自己的 Gitee token：

```bash
python main.py --init-config
# 编辑 gitee-downloader.yaml，把 YOUR_GITEE_TOKEN 替换为真实 token
python main.py
```

也可以使用环境变量提供 token：

```powershell
$env:GITEE_TOKEN="your-token"
python main.py
```

常用命令：

```bash
python main.py
python main.py --config gitee-downloader.yaml
python main.py --tag v0.9.164
python main.py --file-filter "*.tar.gz"
python main.py --output-dir ./packages
python main.py --owner other-user --repo other-repo --token YOUR_TOKEN
```

## 配置

默认会自动查找以下配置文件：

- `gitee-downloader.yaml`
- `gitee-downloader.yml`
- `gitee-downloader.json`
- `.gitee-downloader.yaml`
- `.gitee-downloader.yml`
- `.gitee-downloader.json`

示例：

```yaml
base_url: https://gitee.com/api/v5
token: YOUR_GITEE_TOKEN
owner: bio-sense
repo: icp-monitoring-app
output_dir: ./downloads
timeout: 30
download_timeout: 60
chunk_size: 8192
file_filter: "*"
auto_extract: true
auto_rename: true
```

Token 优先级：

```text
命令行 --token > 环境变量 GITEE_TOKEN > 配置文件 token > 空字符串
```

`YOUR_GITEE_TOKEN` 是占位符，不会作为真实 token 使用。真实的 `gitee-downloader.yaml` 是本地配置文件，已在 `.gitignore` 中忽略；仓库中只保留 `gitee-downloader.example.yaml` 示例。

## 输出目录

默认下载到 `./downloads`。该目录是运行产物，已在 `.gitignore` 中忽略。

常见输出：

```text
处理完成: 1/1
下载 1 个
跳过 1 个
```

## 开发检查

```bash
python -m compileall -q main.py gitee_downloader
python main.py --help
```
