from django.test import TestCase, RequestFactory
from django_rest_exception_logger.middleware import ExceptionMiddleware


class ExceptionMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_process_exception(self):
        request = self.factory.get('/')
        middleware = ExceptionMiddleware(get_response=lambda r: r)

        response = middleware.process_exception(request, Exception("Test Error"))

        self.assertEqual(response.status_code, 500)
        self.assertIn('error_message', response.json())
