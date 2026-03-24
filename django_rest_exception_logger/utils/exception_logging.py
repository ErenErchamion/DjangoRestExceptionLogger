"""Utilities to persist exceptions into :class:`~django_rest_exception_logger.models.ExceptionLog`.

The logger is intentionally defensive: it should not raise while handling
another exception.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, Optional

from django.urls import resolve

from ..models import ExceptionLog
from .request_data import extract_payload_for_logging, querydict_to_dict, safe_json_dumps


def _safe_resolve_view_name(request: Any) -> str:
    try:
        view_info = resolve(getattr(request, "path_info", "") or "")
        return getattr(view_info, "view_name", None) or "Unknown View"
    except Exception:
        return "Unknown View"


def log_exception(
    exception: BaseException,
    *,
    request: Any = None,
    message: Optional[str] = None,
    full_message: Optional[str] = None,
    log_type: str = "error",
    view_name: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Optional[ExceptionLog]:
    """Create an :class:`~django_rest_exception_logger.models.ExceptionLog` record.

    Args:
        exception: Exception instance to persist.
        request: Optional Django/DRF request object.
        message: Optional override for ``ExceptionLog.message``.
        full_message: Optional override for ``ExceptionLog.full_message``.
        log_type: One of the model's ``LOG_CHOICES``.
        view_name: Optional override for view name.
        extra: Optional dict stored under ``"_extra"`` in ``request_payload``.

    Returns:
        The created model instance, or ``None`` if logging fails.
    """

    try:
        error_type = type(exception).__name__
        error_message = str(exception) if message is None else str(message)
        traceback_text = traceback.format_exc() if full_message is None else str(full_message)

        if request is not None:
            resolved_view = view_name or _safe_resolve_view_name(request)
            headers_obj = getattr(request, "headers", None) or {}
            params_obj = getattr(request, "GET", None) or {}
            payload_obj = extract_payload_for_logging(request)
        else:
            resolved_view = view_name or "Unknown View"
            headers_obj = {}
            params_obj = {}
            payload_obj = ""

        # Serialize safely to TextField-friendly JSON strings.
        headers = safe_json_dumps(dict(headers_obj)) if headers_obj else ""
        params = safe_json_dumps(querydict_to_dict(params_obj)) if params_obj else ""

        payload_data: Any = payload_obj

        if extra:
            if isinstance(payload_data, dict):
                payload_data = {**payload_data, "_extra": extra}
            elif payload_data in ("", None):
                payload_data = {"_extra": extra}
            else:
                payload_data = {"_payload": payload_data, "_extra": extra}

        payload = payload_data if isinstance(payload_data, str) else safe_json_dumps(payload_data)

        exception_log = ExceptionLog.objects.create(
            message=error_message,
            full_message=traceback_text,
            error_type=error_type,
            log_type=log_type,
            view_name=resolved_view,
            request_payload=payload,
            request_headers=headers,
            request_params=params,
        )

        # Attach user when present.
        try:
            if request is not None and hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
                exception_log.user = request.user
                exception_log.save(update_fields=["user"])
        except Exception:
            # Never raise during logging.
            pass

        return exception_log
    except Exception:
        return None

