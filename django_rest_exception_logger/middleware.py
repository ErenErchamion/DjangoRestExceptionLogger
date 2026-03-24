from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin

from .utils import log_exception


class ExceptionMiddleware(MiddlewareMixin):
    """Log unhandled exceptions with request context."""

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def __call__(self, request):
        # Cache request body defensively for later logging.
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

        error_type = type(exception).__name__

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

        exception_log = log_exception(
            exception,
            request=request,
            log_type="error",
            view_name=view_name,
        )

        # If logging fails for any reason, still return a stable response.
        log_id = getattr(exception_log, "id", None)
        return JsonResponse({"error_message": "An error occurred", "log_id": log_id}, status=500)
