import time
import uuid
import json
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging_utils import setup_logger, APIFormatter, SensitiveDataMasker
from app.core.console_output import print_step_start, print_step_end, print_success, print_error, print_warning, console


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        logger_name: str = "api",
        log_request_body: bool = True,
        log_response_body: bool = True,
        log_headers: bool = False,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.logger = setup_logger(
            logger_name,
            json_format=True,
            max_bytes=10 * 1024 * 1024,
            backup_count=5,
            console_output=False
        )
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.log_headers = log_headers
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()

        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")

        user_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)

        path_params = request.path_params
        query_params = dict(request.query_params)

        request_body = None
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                try:
                    request_body = json.loads(body.decode())
                    request_body = SensitiveDataMasker.mask_dict(request_body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    request_body = "[Unable to parse body]"
            request._body = body

        log_data = {
            "request_timestamp": datetime.fromtimestamp(
                request.state.start_time, tz=timezone.utc
            ).isoformat(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "path_params": path_params,
            "query_params": query_params,
            "request_body": request_body,
            "user_id": str(user_id) if user_id else None,
            "client_ip": client_ip,
            "user_agent": user_agent,
        }

        if self.log_headers:
            log_data["headers"] = dict(request.headers)

        print_step_start(f"{request.method} {request.url.path}", "API")

        response: Response = None
        response_body = None
        error_message = None
        exc_info = None

        try:
            response = await call_next(request)

            if self.log_response_body:
                response_body = response.body.decode() if hasattr(response, "body") else None
                if response_body:
                    try:
                        response_body = json.loads(response_body)
                        response_body = SensitiveDataMasker.mask_dict(response_body)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass

            duration_ms = round((time.time() - request.state.start_time) * 1000, 2)

            log_data.update({
                "response_status": response.status_code,
                "response_body": response_body,
                "duration_ms": duration_ms
            })

            if response.status_code >= 500:
                self.logger.error(
                    f"API Response: {request.method} {request.url.path} - {response.status_code}",
                    extra=log_data,
                    exc_info=exc_info
                )
                print_error(f"HTTP {response.status_code} | {duration_ms}ms | {request.method} {request.url.path}", "API")
            elif response.status_code >= 400:
                self.logger.warning(
                    f"API Response: {request.method} {request.url.path} - {response.status_code}",
                    extra=log_data
                )
                print_warning(f"HTTP {response.status_code} | {duration_ms}ms | {request.method} {request.url.path}", "API")
            else:
                self.logger.info(
                    f"API Response: {request.method} {request.url.path} - {response.status_code}",
                    extra=log_data
                )
                print_success(f"HTTP {response.status_code} | {duration_ms}ms | {request.method} {request.url.path}", "API")

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            exc_info = (type(e), e, e.__traceback__)
            error_message = str(e)
            duration_ms = round((time.time() - request.state.start_time) * 1000, 2)

            log_data.update({
                "response_status": 500,
                "error_message": error_message,
                "duration_ms": duration_ms
            })

            self.logger.error(
                f"API Error: {request.method} {request.url.path}",
                extra=log_data,
                exc_info=exc_info
            )
            print_error(f"Exception | {duration_ms}ms | {request.method} {request.url.path} - {error_message[:50]}", "API")

            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
                headers={"X-Request-ID": request_id}
            )


class BusinessLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = setup_logger(
            "business",
            json_format=True,
            max_bytes=10 * 1024 * 1024,
            backup_count=5
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.business_log = {
            "operation": None,
            "entity_type": None,
            "entity_id": None,
            "details": {}
        }
        return await call_next(request)


def log_business_operation(
    logger_name: str = "business",
    operation: str = None,
    entity_type: str = None,
    entity_id: str = None,
    details: dict = None,
    level: str = "info"
):
    logger = logging.getLogger(logger_name)
    log_data = {
        "operation": operation,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
        "details": SensitiveDataMasker.mask_dict(details or {}),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"Business Operation: {operation}", extra=log_data)


import logging
