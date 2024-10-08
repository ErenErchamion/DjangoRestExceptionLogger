# Django Rest Exception Logger

This package provides middleware for automatically logging exceptions in Django applications. It captures and stores exception details such as the error message, stack trace, request data, headers, and the view where the error occurred.

## Features

- Automatically logs exceptions in the database
- Captures request payloads and headers for debugging
- Customizable via model relationships with your user model
- Handles specific exceptions like `PermissionDenied` and `ParseError` with customized responses

## Requirements

- Python 3.8+
- Django 3.2+
- Django Rest Framework 3.12+

## Installation

1. **Install the package**

   You can install this package from PyPI using pip:

   ```bash
   pip install django-exception-logger
   ```

2. **Add the middleware**

   To enable automatic exception logging, add `ExceptionMiddleware` to your `MIDDLEWARE` list in your Django project's `settings.py` file:

   ```python
   MIDDLEWARE = [
       # Other middlewares...
       'django_exception_logger.middleware.ExceptionMiddleware',
   ]
   ```

3. **Add the ExceptionLog model**

   This package comes with the `ExceptionLog` model, which stores information about exceptions. You need to integrate it into your project.

   - Add `exception_logging` to the `INSTALLED_APPS` list in `settings.py`:

     ```python
     INSTALLED_APPS = [
         # Other apps...
         'django_exception_logger',
     ]
     ```

   - Run migrations to create the necessary database tables:

     ```bash
     python manage.py migrate
     ```
   - if migration not detected, run this command
     ```bash
      python manage.py makemigrations django_exception_logger
     ```
       

4. **Configure the user model (optional)**

   By default, the `ExceptionLog` model has a foreign key to the `auth.User` model. If you are using a custom user model, ensure that the `ExceptionLog` model's `user` field is compatible with your custom user model.

5. **Customize Middleware behavior (optional)**

   You can extend the `ExceptionMiddleware` or modify it to add additional custom exception handling as needed for your application.

## Usage

Once the middleware is installed, it will automatically log exceptions that occur in your views to the `ExceptionLog` model. The logged information will include:

- Exception type and message
- Full traceback
- Request payload (for POST, PUT, PATCH requests)
- Request headers and parameters
- View name where the exception occurred
- User who initiated the request (if available)

### Usage Examples

```python
# 1. Query All Error Logs
from django_rest_exception_logger.models import ExceptionLog

# Retrieve all error logs ordered by most recent
error_logs = ExceptionLog.objects.filter(log_type="error").order_by('-timestamp')

for log in error_logs:
    print(log.message, log.timestamp)

# 2. Create a New Info Log
from django_rest_exception_logger.models import ExceptionLog

# Create a new info log entry
ExceptionLog.objects.create(
    log_type="info",
    message="This is an informational log",
    view_name="my_view"
)

```

## Example Use Cases

- **Debugging Production Issues**: Track unexpected errors in production environments with full context, including which user triggered the error and what data they sent.
- **Security Auditing**: Capture unauthorized access attempts and permission errors for analysis and potential remediation.
- **Improving User Experience**: With detailed logs, identify common errors and enhance your application's stability and error handling.

## Testing

To test the functionality of the middleware, you can manually raise an exception in one of your views and check the logs in your admin or database:

```python
def test_view(request):
    raise Exception("Test exception for logging")
```

After visiting this view, a new entry should appear in the `ExceptionLog` model, capturing the details of the error.

## Contributing

Feel free to open an issue or submit a pull request if you have suggestions for improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
