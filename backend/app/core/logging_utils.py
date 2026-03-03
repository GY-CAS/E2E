import logging
import json
import re
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
from pathlib import Path

from app.core.config import settings


class ColoredConsoleHandler(StreamHandler):
    COLORS = {
        'DEBUG': '\033[90m',
        'INFO': '\033[96m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'CRITICAL': '\033[95m',
    }
    RESET = '\033[0m'

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            level = record.levelname
            color = self.COLORS.get(level, '')

            if sys.stdout.isatty() and color:
                msg = f"{color}{msg}{self.RESET}"

            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


class SensitiveDataMasker:
    SENSITIVE_KEYS = {
        "password", "passwd", "pwd", "secret", "token", "api_key", "apikey",
        "access_key", "accesskey", "private_key", "privatekey", "secret_key",
        "credential", "authorization", "auth_token", "refresh_token",
        "session_id", "sessionid", "jwt", "bearer", "x-api-key",
        "minio_access_key", "minio_secret_key", "llm_api_key", "embedding_api_key",
        "secret_key", "encryption_key", "salt"
    }

    SENSITIVE_PATTERNS = [
        (r'(["\']?)(password|passwd|pwd|secret|token)(["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)(["\']?)', r'\1\2\3***REDACTED***\5'),
        (r'(bearer\s+)([a-zA-Z0-9\-_.~+/]+=*)', r'\1***REDACTED***'),
        (r'(token["\']?\s*[:=]\s*["\']?)([a-zA-Z0-9\-_.~+/]+=*)(["\']?)', r'\1***REDACTED***\3'),
        (r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)(["\']?)', r'\1***REDACTED***\3'),
    ]

    @classmethod
    def mask_value(cls, value: Any) -> Any:
        if isinstance(value, str):
            for pattern, replacement in cls.SENSITIVE_PATTERNS:
                value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
            return value
        elif isinstance(value, dict):
            return cls.mask_dict(value)
        elif isinstance(value, list):
            return [cls.mask_value(item) for item in value]
        return value

    @classmethod
    def mask_dict(cls, data: Dict) -> Dict:
        if not isinstance(data, dict):
            return data

        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            if key_lower in cls.SENSITIVE_KEYS or any(s in key_lower for s in cls.SENSITIVE_KEYS):
                masked[key] = "***REDACTED***"
            else:
                masked[key] = cls.mask_value(value)
        return masked


class JSONFormatter(logging.Formatter):
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if self.include_extra:
            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in logging.LogRecord(
                    "", 0, "", 0, "", (), None
                ).__dict__ and not k.startswith('_')
            }
            if extra_fields:
                log_data["extra"] = SensitiveDataMasker.mask_dict(extra_fields)

        return json.dumps(log_data, ensure_ascii=False, default=str)


class APIFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }

        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in logging.LogRecord(
                "", 0, "", 0, "", (), None
            ).__dict__ and not k.startswith('_')
        }

        api_fields = [
            "request_timestamp", "method", "path", "path_params", "query_params",
            "request_body", "response_status", "response_body", "duration_ms",
            "user_id", "client_ip", "user_agent", "request_id"
        ]

        for field in api_fields:
            if field in extra_fields:
                log_data[field] = SensitiveDataMasker.mask_value(extra_fields[field])

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["error_message"] = str(record.exc_info[1]) if record.exc_info[1] else None

        return json.dumps(log_data, ensure_ascii=False, default=str)


def get_log_file_path(log_type: str = "app") -> str:
    log_dir = getattr(settings, 'LOG_DIR', './logs')
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"{log_type}.log")


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[str] = None,
    json_format: bool = False,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level or settings.LOG_LEVEL))

    if logger.handlers:
        return logger

    if console_output:
        console_handler = ColoredConsoleHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    if json_format or getattr(settings, 'LOG_JSON_FORMAT', False):
        file_handler = RotatingFileHandler(
            log_file or get_log_file_path(name.split('.')[-1] or "app"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    elif log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
