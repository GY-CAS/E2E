import sys
import logging
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from enum import Enum

class ConsoleColor(Enum):
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class ConsolePrinter:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._verbose = True
        self._use_colors = True

    def set_verbose(self, verbose: bool):
        self._verbose = verbose

    def set_colors(self, use_colors: bool):
        self._use_colors = use_colors

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def _colorize(self, text: str, color: ConsoleColor) -> str:
        if not self._use_colors or not sys.stdout.isatty():
            return text
        return f"{color.value}{text}{ConsoleColor.RESET.value}"

    def _format_message(
        self,
        message: str,
        module: str = None,
        level: str = None,
        color: ConsoleColor = None
    ) -> str:
        timestamp = self._get_timestamp()
        module_str = f"[{module}]" if module else ""
        level_str = f"[{level}]" if level else ""

        parts = [f"{self._colorize(timestamp, ConsoleColor.GRAY)}"]
        if module_str:
            parts.append(self._colorize(module_str, ConsoleColor.CYAN))
        if level_str:
            parts.append(self._colorize(level_str, ConsoleColor.YELLOW))
        parts.append(message)

        full_message = " ".join(parts)
        if color:
            full_message = self._colorize(full_message, color)

        return full_message

    def print(self, message: str, module: str = None):
        if not self._verbose:
            return
        print(self._format_message(message, module))

    def info(self, message: str, module: str = None):
        if not self._verbose:
            return
        print(self._format_message(message, module, "INFO", ConsoleColor.BLUE))

    def success(self, message: str, module: str = None):
        if not self._verbose:
            return
        print(self._format_message(message, module, "OK", ConsoleColor.GREEN))

    def warning(self, message: str, module: str = None):
        if not self._verbose:
            return
        print(self._format_message(message, module, "WARN", ConsoleColor.YELLOW))

    def error(self, message: str, module: str = None):
        if not self._verbose:
            return
        print(self._format_message(message, module, "ERROR", ConsoleColor.RED))

    def debug(self, message: str, module: str = None):
        if not self._verbose:
            return
        print(self._format_message(message, module, "DEBUG", ConsoleColor.GRAY))

    def step_start(self, step_name: str, module: str = None):
        if not self._verbose:
            return
        msg = f"▶ 开始执行 [{step_name}]"
        print(self._format_message(msg, module, "START", ConsoleColor.MAGENTA))

    def step_end(self, step_name: str, result: str = None, module: str = None):
        if not self._verbose:
            return
        msg = f"✓ [{step_name}] 执行完成"
        if result:
            msg += f"，结果：{result}"
        print(self._format_message(msg, module, "DONE", ConsoleColor.GREEN))

    def step_progress(self, current: int, total: int, message: str = None, module: str = None):
        if not self._verbose:
            return
        msg = f"进度：{current}/{total}"
        if message:
            msg += f" - {message}"
        print(self._format_message(msg, module, "PROGRESS", ConsoleColor.CYAN))

    def divider(self, title: str = None):
        if not self._verbose:
            return
        if title:
            width = 60
            half = (width - len(title) - 2) // 2
            line = "=" * half + " " + title + " " + "=" * half
            print(self._colorize(line[:width], ConsoleColor.BOLD))
        else:
            print(self._colorize("=" * 60, ConsoleColor.BOLD))


console = ConsolePrinter()


def print_step_start(operation: str, module: str = None):
    console.step_start(operation, module)


def print_step_end(operation: str, result: str = None, module: str = None):
    console.step_end(operation, result, module)


def print_info(message: str, module: str = None):
    console.info(message, module)


def print_success(message: str, module: str = None):
    console.success(message, module)


def print_warning(message: str, module: str = None):
    console.warning(message, module)


def print_error(message: str, module: str = None):
    console.error(message, module)


def print_progress(current: int, total: int, message: str = None, module: str = None):
    console.step_progress(current, total, message, module)


def print_divider(title: str = None):
    console.divider(title)
