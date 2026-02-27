"""Request data extraction helpers.

The middleware in this package runs while Django is already handling an exception.
It must never raise while collecting debug context. All helpers in this module are
best-effort and defensive by design.

Nothing here should read uploaded file bytes. For unknown/binary bodies we only
store a short, UTF-8 decoded preview with replacement characters.
"""

from __future__ import annotations

import json
from io import BytesIO
from typing import Any, Dict

from django.utils.datastructures import MultiValueDict


def querydict_to_dict(qd: Any) -> Dict[str, Any]:
    """Convert a QueryDict/MultiValueDict-like object into a regular ``dict``.

    - When multi-values exist, values are returned as lists.
    - For unknown types, falls back to ``dict(qd)`` and ultimately ``str(qd)``.

    This function is intentionally tolerant because request objects can differ
    between Django/DRF versions and test doubles.
    """

    if qd is None:
        return {}

    if hasattr(qd, "lists"):
        try:
            return {k: v for k, v in qd.lists()}
        except Exception:
            return {"_unserializable": str(qd)}

    if isinstance(qd, MultiValueDict):
        try:
            return {k: qd.getlist(k) for k in qd.keys()}
        except Exception:
            return {"_unserializable": str(qd)}

    try:
        return dict(qd)
    except Exception:
        return {"_unserializable": str(qd)}


def safe_json_dumps(value: Any) -> str:
    """Serialize ``value`` into a JSON string.

    Uses ``default=str`` to avoid crashes on non-JSON types.
    Falls back to ``str(value)`` on any serialization error.
    """

    try:
        return json.dumps(value, default=str, ensure_ascii=False)
    except Exception:
        return str(value)


def summarize_files(files: Any) -> Dict[str, Any]:
    """Return a metadata-only summary for uploaded files.

    The middleware must not read file content; it only logs safe attributes.
    """

    if not files:
        return {}

    summary: Dict[str, Any] = {}

    try:
        keys = list(files.keys())
    except Exception:
        keys = []

    for key in keys:
        try:
            file_list = files.getlist(key) if hasattr(files, "getlist") else [files[key]]
        except Exception:
            continue

        summarized = []
        for f in file_list:
            try:
                summarized.append(
                    {
                        "name": getattr(f, "name", None),
                        "size": getattr(f, "size", None),
                        "content_type": getattr(f, "content_type", None),
                    }
                )
            except Exception:
                summarized.append({"_unserializable": str(f)})

        summary[key] = summarized if len(summarized) != 1 else summarized[0]

    return summary


def extract_payload_for_logging(request: Any) -> Any:
    """Extract a request payload suitable for persistence in a TextField.

    Behavior:
    - For DRF requests, prefer ``request.data``.
    - For multipart requests, log form fields + *file metadata*.
    - For JSON requests, attempt to parse and fall back to parse error metadata.
    - For unknown/binary content, store a small safe preview.

    This function is best-effort and must not raise.
    """

    content_type = (getattr(request, "content_type", None) or "").lower()

    # DRF Requests: request.data already handles JSON/form-data and respects parsers.
    # Import DRF lazily so importing this package doesn't require configured settings.
    try:
        from rest_framework.request import Request as DRFRequest  # type: ignore
    except Exception:  # pragma: no cover
        DRFRequest = None  # type: ignore

    if DRFRequest is not None and isinstance(request, DRFRequest):
        try:
            return request.data
        except Exception as exc:
            return {"_parse_error": str(exc), "content_type": content_type}

    if "multipart/form-data" in content_type:
        try:
            fields = querydict_to_dict(getattr(request, "POST", None))
        except Exception:
            fields = {}

        try:
            files_summary = summarize_files(getattr(request, "FILES", None))
        except Exception:
            files_summary = {}

        return {"fields": fields, "files": files_summary, "content_type": content_type}

    if "application/x-www-form-urlencoded" in content_type:
        return {"fields": querydict_to_dict(getattr(request, "POST", None)), "content_type": content_type}

    body_bytes = getattr(request, "request_body", None)
    if body_bytes is None:
        return ""

    if "application/json" in content_type or content_type.endswith("+json"):
        try:
            from rest_framework.parsers import JSONParser  # type: ignore

            stream = BytesIO(body_bytes)
            return JSONParser().parse(stream)
        except Exception as exc:
            preview = body_bytes[:512].decode("utf-8", errors="replace") if body_bytes else ""
            return {
                "_parse_error": str(exc),
                "content_type": content_type,
                "body_length": len(body_bytes),
                "body_preview": preview,
            }

    return {
        "content_type": content_type,
        "body_length": len(body_bytes),
        "body_preview": body_bytes[:512].decode("utf-8", errors="replace") if body_bytes else "",
    }
