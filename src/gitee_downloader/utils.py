"""工具函数模块"""

import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Dict


def setup_windows_encoding() -> None:
    """修复 Windows 控制台中文乱码"""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# 匹配 ANSI 转义码的正则
_ANSI_ESCAPE_RE = re.compile(r"\033\[[0-9;]*m")


def visible_width(text: str) -> int:
    """计算字符串在终端中的可见宽度（去除 ANSI 转义码）"""
    clean = _ANSI_ESCAPE_RE.sub("", text)
    width = 0
    for char in clean:
        if unicodedata.combining(char):
            continue
        if unicodedata.east_asian_width(char) in ("F", "W"):
            width += 2
        else:
            width += 1
    return width


def _char_width(char: str) -> int:
    """计算单个字符的终端显示宽度。"""
    if unicodedata.combining(char):
        return 0
    return 2 if unicodedata.east_asian_width(char) in ("F", "W") else 1


def truncate_visible(text: str, max_width: int) -> str:
    """截断字符串到指定的可见宽度，保留 ANSI 颜色码"""
    clean = _ANSI_ESCAPE_RE.sub("", text)
    if len(clean) <= max_width:
        return text
    # 找到可见字符达到 max_width 时的位置
    visible_count = 0
    result = []
    i = 0
    while i < len(text):
        # 检查是否是 ANSI 转义码
        if text[i] == "\033" and i + 1 < len(text) and text[i + 1] == "[":
            # 找到 m 结束
            end = text.find("m", i)
            if end != -1:
                result.append(text[i:end + 1])
                i = end + 1
                continue
        if visible_count >= max_width:
            break
        char_width = _char_width(text[i])
        if visible_count + char_width > max_width:
            break
        result.append(text[i])
        visible_count += char_width
        i += 1
    return "".join(result)


def is_already_downloaded(save_path: Path) -> bool:
    """检查文件是否已下载（文件存在且大小大于0）"""
    return save_path.exists() and save_path.stat().st_size > 0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes < 0:
        raise ValueError("size_bytes must be non-negative")

    value = float(size_bytes)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024


def build_headers(token: str) -> Dict[str, str]:
    """生成 API / 下载请求头"""
    return {"PRIVATE-TOKEN": token} if token else {}


class Logger:
    """美化版日志记录器"""

    # ANSI 颜色代码
    RESET = "\033[0m"
    GRAY = "\033[90m"    # 深灰色 - 操作提示
    CYAN = "\033[36m"    # 青色 - 关键信息高亮
    YELLOW = "\033[33m"  # 黄色 - 路径
    GREEN = "\033[32m"   # 绿色 - 成功
    RED = "\033[31m"     # 红色 - 错误
    MAGENTA = "\033[35m" # 洋红 - 跳过

    # 丰富的 Unicode 图标
    ICON_CONFIG = "⚙"      # 配置
    ICON_FETCH = "📡"      # 获取
    ICON_RENAME = "✏"     # 重命名
    ICON_SUCCESS = "✔"     # 成功
    ICON_SKIP = "-"       # 跳过
    ICON_WARN = "⚠"        # 警告
    ICON_ERROR = "✖"       # 错误
    ICON_FOLDER = "📁"     # 文件夹

    @staticmethod
    def _print(message: str, file=None, end: str = "\n") -> None:
        """安全打印，避免未初始化 UTF-8 控制台时因 emoji 输出失败。"""
        stream = file or sys.stdout
        try:
            print(message, file=stream, end=end)
        except UnicodeEncodeError:
            encoding = getattr(stream, "encoding", None) or "utf-8"
            safe_message = message.encode(encoding, errors="replace").decode(
                encoding, errors="replace"
            )
            stream.write(safe_message + end)
            stream.flush()

    @staticmethod
    def info(message: str, icon: str = None) -> None:
        """操作提示（深灰色）"""
        icon = icon or Logger.ICON_FETCH
        Logger._print(f"{Logger.GRAY}{icon} {message}{Logger.RESET}")

    @staticmethod
    def step(message: str) -> None:
        """阶段分隔线"""
        Logger._print(f"{Logger.GRAY}━━ {message}{Logger.RESET}")

    @staticmethod
    def path(message: str) -> None:
        """路径信息（黄色）"""
        Logger._print(f"{Logger.YELLOW}{Logger.ICON_FOLDER} {message}{Logger.RESET}")

    @staticmethod
    def warning(message: str) -> None:
        """警告（黄色 + ⚠）"""
        Logger._print(f"{Logger.YELLOW}{Logger.ICON_WARN} {message}{Logger.RESET}", file=sys.stderr)

    @staticmethod
    def error(message: str) -> None:
        """错误（红色 + ✖）"""
        Logger._print(f"{Logger.RED}{Logger.ICON_ERROR} {message}{Logger.RESET}", file=sys.stderr)

    @staticmethod
    def success(message: str) -> None:
        """成功结果（绿色 + ✔）"""
        Logger._print(f"{Logger.GREEN}{Logger.ICON_SUCCESS} {message}{Logger.RESET}")

    @staticmethod
    def skip(message: str) -> None:
        """跳过（洋红色 + ⏭）"""
        Logger._print(f"{Logger.MAGENTA}{Logger.ICON_SKIP} {message}{Logger.RESET}")

    @staticmethod
    def skipped_item(name: str, reason: str = "已存在") -> None:
        """跳过单个项目。"""
        Logger._print(
            f"{Logger.MAGENTA}{Logger.ICON_SKIP}{Logger.RESET} "
            f"{Logger.GRAY}{name}{Logger.RESET} {Logger.GRAY}({reason}){Logger.RESET}"
        )

    @staticmethod
    def success_item(name: str, detail: str = None) -> None:
        """成功处理单个项目。"""
        suffix = f" {Logger.GRAY}({detail}){Logger.RESET}" if detail else ""
        Logger._print(f"{Logger.GREEN}{Logger.ICON_SUCCESS}{Logger.RESET} {Logger.CYAN}{name}{Logger.RESET}{suffix}")

    @staticmethod
    def inline_status(icon: str, message: str, end: str = "\n") -> None:
        """打印不带固定语义的状态行。"""
        Logger._print(f"{Logger.GRAY}{icon}{Logger.RESET} {message}", end=end)


class ProgressBar:
    """终端下载进度条"""

    # 进度条格数（固定单档布局）
    BAR_WIDTH = 20
    # 文件名截断宽度
    NAME_WIDTH = 40

    def __init__(self, filename: str, total_size: int = 0):
        """
        Args:
            filename: 文件名
            total_size: 文件总大小（字节），0 表示未知
        """
        self.filename = filename
        self.total_size = total_size
        self.downloaded = 0
        self.start_time = time.time()
        self.last_print_time = 0

    def update(self, chunk_size: int) -> None:
        """更新已下载字节数"""
        self.downloaded += chunk_size
        now = time.time()
        # 限制刷新频率，最多每 0.1 秒刷新一次
        if now - self.last_print_time < 0.1:
            return
        self.last_print_time = now
        self._render()

    def finish(self) -> None:
        """下载完成，打印最终状态"""
        self._render(force=True)
        # 换行，避免后续输出覆盖进度条
        print()

    def _render(self, force: bool = False) -> None:
        """渲染进度条到终端 - npm 风格"""
        elapsed = time.time() - self.start_time
        speed = self.downloaded / elapsed if elapsed > 0 else 0

        RESET = "\033[0m"
        GRAY = "\033[90m"

        # 百分比和大小
        if self.total_size > 0:
            percent = min(self.downloaded / self.total_size, 1.0)
            percent_str = f"{int(percent * 100)}"
            size_str = format_file_size(self.total_size)
        else:
            percent = 0
            percent_str = "?"
            size_str = "?"

        # 速度和耗时
        speed_str = format_file_size(int(speed))
        speed_display = f"{speed_str}/s"
        if elapsed < 60:
            elapsed_str = f"{elapsed:.1f}s"
        else:
            elapsed_str = f"{elapsed / 60:.1f}m"

        # 进度条颜色：进行中蓝色，完成时绿色
        if self.total_size > 0:
            if percent >= 1.0:
                bar_color = "\033[32m"  # 绿色
            else:
                bar_color = "\033[34m"  # 蓝色
        else:
            bar_color = GRAY

        # 文件名截断到固定宽度
        display_name = truncate_visible(self.filename, self.NAME_WIDTH)
        if len(self.filename) > len(display_name):
            display_name += "..."

        # 生成进度条
        filled_char = "█"
        empty_char = "░"
        try:
            (filled_char + empty_char).encode(sys.stdout.encoding or "utf-8")
        except UnicodeEncodeError:
            filled_char = "#"
            empty_char = "-"

        filled = int(self.BAR_WIDTH * percent) if self.total_size > 0 else 0
        bar = f"{bar_color}{filled_char * filled}{GRAY}{empty_char * (self.BAR_WIDTH - filled)}{RESET}"

        stats = [f"{percent_str.rjust(3)}%", size_str, speed_display, elapsed_str]
        stats_text = f" {GRAY}|{RESET} ".join(stats)

        # 组装行
        line = f"{display_name} [{bar}] {stats_text}"

        try:
            sys.stdout.write(f"\r{line}")
        except UnicodeEncodeError:
            encoding = sys.stdout.encoding or "utf-8"
            safe_line = line.encode(encoding, errors="replace").decode(
                encoding, errors="replace"
            )
            sys.stdout.write(f"\r{safe_line}")
        sys.stdout.flush()
