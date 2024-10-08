import traceback
from io import BytesIO
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from .models import ExceptionLog
class ExceptionMiddleware(MiddlewareMixin):
    """
    Middleware to log exceptions in a Django application.
    It captures request data, exception details, and saves them in the ExceptionLog model.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request body for logging in case of POST, PUT, or PATCH requests
        if request.method in ('POST', 'PUT', 'PATCH'):
            request.request_body = request.body
        else:
            request.request_body = None

        # Process the request
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Process any exceptions that occur during the request and log them.
        Specific handling for `PermissionDenied` and `ParseError`.
        """
        error_message = str(exception)
        error_type = type(exception).__name__
        traceback_text = traceback.format_exc()

        # Handle specific exception types
        if isinstance(exception, PermissionDenied):
            return JsonResponse({"error": "You do not have permission to perform this action"}, status=403)
        elif error_type == 'ParseError':
            return JsonResponse({"error": "Invalid data format"}, status=400)

        # Resolve view information for logging
        view_info = resolve(request.path_info)
        view_name = view_info.view_name if view_info else "Unknown View"

        # Extract request headers, parameters, and payload
        headers = request.headers if hasattr(request, 'headers') else ""
        params = request.GET if hasattr(request, 'GET') else ""

        payload = ""
        try:
            if isinstance(request, Request):
                payload = request.data  # Django Rest Framework request
            elif request.request_body is not None:
                # For standard Django requests, parse the body manually
                stream = BytesIO(request.request_body)
                data = JSONParser().parse(stream)
                payload = data
        except Exception:
            # Fallback to raw body if JSON parsing fails
            payload = request.request_body.decode('utf-8') if request.request_body else ""

        # Log the exception
        exception_log = ExceptionLog.objects.create(
            message=error_message,
            full_message=traceback_text,
            error_type=error_type,
            log_type="error",
            view_name=view_name,
            request_payload=payload,
            request_headers=headers,
            request_params=params
        )

        # Associate user with the log if available
        if hasattr(request, 'user') and request.user.is_authenticated:
            exception_log.user = request.user
            exception_log.save()

        # Return a generic error response
        return JsonResponse({"error_message": "An error occurred", "log_id": exception_log.id}, status=500)