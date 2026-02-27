import traceback

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin

from .models import ExceptionLog
from .utils import extract_payload_for_logging, querydict_to_dict, safe_json_dumps


class ExceptionMiddleware(MiddlewareMixin):
    """Persist unhandled exceptions with request context.

    This middleware is intended for production use:

    - It must never raise while handling another exception.
    - It avoids reading uploaded file bytes.
    - It stores request headers/params/payload as JSON strings (TextField-friendly).

    Notes
    -----
    - PermissionDenied returns a 403 JSON response and is *not* logged.
    - DRF ParseError returns a 400 JSON response and is *not* logged.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Cache request body for later logging. Accessing request.body can raise
        # if the stream was already consumed or if the body is malformed.
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                request.request_body = request.body
            except Exception:
                request.request_body = None
        else:
            request.request_body = None

        return self.get_response(request)

    def process_exception(self, request, exception):
        """Log the exception and return a JSON error response."""

        error_message = str(exception)
        error_type = type(exception).__name__
        traceback_text = traceback.format_exc()

        if isinstance(exception, PermissionDenied):
            return JsonResponse({"error": "You do not have permission to perform this action"}, status=403)
        if error_type == "ParseError":
            return JsonResponse({"error": "Invalid data format"}, status=400)

        # Resolve view name. resolve() itself can raise (e.g., Resolver404).
        try:
            view_info = resolve(request.path_info)
            view_name = getattr(view_info, "view_name", None) or "Unknown View"
        except Exception:
            view_name = "Unknown View"

        headers_obj = request.headers if hasattr(request, "headers") else {}
        params_obj = request.GET if hasattr(request, "GET") else {}
        payload_obj = extract_payload_for_logging(request)

        headers = safe_json_dumps(dict(headers_obj)) if headers_obj else ""
        params = safe_json_dumps(querydict_to_dict(params_obj)) if params_obj else ""
        payload = payload_obj if isinstance(payload_obj, str) else safe_json_dumps(payload_obj)

        exception_log = ExceptionLog.objects.create(
            message=error_message,
            full_message=traceback_text,
            error_type=error_type,
            log_type="error",
            view_name=view_name,
            request_payload=payload,
            request_headers=headers,
            request_params=params,
        )

        if hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
            exception_log.user = request.user
            exception_log.save(update_fields=["user"])

        return JsonResponse({"error_message": "An error occurred", "log_id": exception_log.id}, status=500)
