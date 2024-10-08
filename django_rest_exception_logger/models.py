# Model for logging exceptions
from django.db import models


class ExceptionLog(models.Model):
    """
    Model to store exception logs, including request details and error information.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    LOG_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("critical", "Critical"),
    ]
    error_type = models.CharField(max_length=255)
    view_name = models.CharField(max_length=255)
    log_type = models.CharField(choices=LOG_CHOICES, max_length=10, default="info")
    message = models.CharField(max_length=5000)
    full_message = models.TextField(default="")
    request_payload = models.TextField(default="")
    request_params = models.TextField(default="")
    request_headers = models.TextField(default="")
    user = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.error_type} - {self.timestamp}"
