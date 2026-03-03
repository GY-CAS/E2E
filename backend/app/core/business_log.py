import functools
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from app.core.logging_utils import SensitiveDataMasker, setup_logger


class BusinessLogger:
    def __init__(self, name: str = "business"):
        self.logger = setup_logger(name, json_format=True)

    def log(
        self,
        operation: str,
        entity_type: str = None,
        entity_id: str = None,
        details: Dict[str, Any] = None,
        level: str = "info",
        user_id: str = None,
        request_id: str = None
    ):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "details": SensitiveDataMasker.mask_dict(details or {}),
        }

        if user_id:
            log_data["user_id"] = str(user_id)
        if request_id:
            log_data["request_id"] = str(request_id)

        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(f"Business: {operation}", extra=log_data)

    def info(self, operation: str, entity_type: str = None, entity_id: str = None, details: Dict[str, Any] = None, **kwargs):
        self.log(operation, entity_type, entity_id, details, "info", **kwargs)

    def warning(self, operation: str, entity_type: str = None, entity_id: str = None, details: Dict[str, Any] = None, **kwargs):
        self.log(operation, entity_type, entity_id, details, "warning", **kwargs)

    def error(self, operation: str, entity_type: str = None, entity_id: str = None, details: Dict[str, Any] = None, **kwargs):
        self.log(operation, entity_type, entity_id, details, "error", **kwargs)

    def debug(self, operation: str, entity_type: str = None, entity_id: str = None, details: Dict[str, Any] = None, **kwargs):
        self.log(operation, entity_type, entity_id, details, "debug", **kwargs)


business_logger = BusinessLogger()


def log_operation(
    operation: str,
    entity_type: str = None,
    include_args: bool = True,
    include_result: bool = True,
    mask_sensitive: bool = True
):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            entity_id = None
            details = {
                "function": func.__name__,
                "args": None,
                "result": None,
                "error": None
            }

            if include_args:
                args_list = list(args)
                if mask_sensitive:
                    args_list = [SensitiveDataMasker.mask_value(arg) for arg in args_list]
                details["args"] = {
                    "args": str(args_list)[0:500],
                    "kwargs": SensitiveDataMasker.mask_dict(kwargs) if mask_sensitive else kwargs
                }

            start_time = datetime.now(timezone.utc)

            try:
                result = await func(*args, **kwargs)

                if hasattr(result, 'id'):
                    entity_id = result.id
                elif isinstance(result, dict) and 'id' in result:
                    entity_id = result.get('id')

                if include_result:
                    result_data = str(result)[0:500] if result else None
                    if mask_sensitive:
                        result_data = SensitiveDataMasker.mask_value(result_data)
                    details["result"] = result_data

                duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                details["duration_ms"] = round(duration_ms, 2)

                business_logger.info(
                    operation=operation,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details=details
                )

                return result

            except Exception as e:
                details["error"] = {
                    "type": type(e).__name__,
                    "message": str(e)
                }
                duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                details["duration_ms"] = round(duration_ms, 2)

                business_logger.error(
                    operation=operation,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details=details
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            entity_id = None
            details = {
                "function": func.__name__,
                "args": None,
                "result": None,
                "error": None
            }

            if include_args:
                args_list = list(args)
                if mask_sensitive:
                    args_list = [SensitiveDataMasker.mask_value(arg) for arg in args_list]
                details["args"] = {
                    "args": str(args_list)[0:500],
                    "kwargs": SensitiveDataMasker.mask_dict(kwargs) if mask_sensitive else kwargs
                }

            start_time = datetime.now(timezone.utc)

            try:
                result = func(*args, **kwargs)

                if hasattr(result, 'id'):
                    entity_id = result.id
                elif isinstance(result, dict) and 'id' in result:
                    entity_id = result.get('id')

                if include_result:
                    result_data = str(result)[0:500] if result else None
                    if mask_sensitive:
                        result_data = SensitiveDataMasker.mask_value(result_data)
                    details["result"] = result_data

                duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                details["duration_ms"] = round(duration_ms, 2)

                business_logger.info(
                    operation=operation,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details=details
                )

                return result

            except Exception as e:
                details["error"] = {
                    "type": type(e).__name__,
                    "message": str(e)
                }
                duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                details["duration_ms"] = round(duration_ms, 2)

                business_logger.error(
                    operation=operation,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details=details
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


import asyncio
