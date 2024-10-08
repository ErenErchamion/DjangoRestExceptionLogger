from django.contrib import admin
from .models import ExceptionLog


class ExceptionLogAdmin(admin.ModelAdmin):
    """
    Admin interface for managing ExceptionLog entries.
    """
    list_display = ('timestamp', 'error_type', 'view_name', 'log_type', 'user')
    list_filter = ('log_type', 'error_type', 'timestamp')
    search_fields = ('error_type', 'view_name', 'message', 'user__username')
    readonly_fields = (
        'timestamp', 'error_type', 'view_name', 'log_type', 'message', 'full_message', 'request_payload',
        'request_params',
        'request_headers', 'user')

    def has_add_permission(self, request):
        # Prevent manual addition of logs in the admin interface
        return False

    def has_change_permission(self, request, obj=None):
        # Make the entries read-only in the admin interface
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow deletion of log entries
        return True


admin.site.register(ExceptionLog, ExceptionLogAdmin)
