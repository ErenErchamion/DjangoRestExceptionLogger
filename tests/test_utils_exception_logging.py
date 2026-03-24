import json

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from django_rest_exception_logger.models import ExceptionLog
from django_rest_exception_logger.utils import log_exception


class LogExceptionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_log_exception_without_request(self):
        log = log_exception(Exception("Boom"), message="Custom")
        self.assertIsNotNone(log)
        self.assertEqual(log.message, "Custom")
        self.assertEqual(log.error_type, "Exception")

    def test_log_exception_stores_extra_inside_payload(self):
        request = self.factory.post("/t/", data=b"{}", content_type="application/json")
        request.request_body = request.body

        log = log_exception(Exception("Boom"), request=request, extra={"a": 1, "b": "x"})
        self.assertIsNotNone(log)

        payload = json.loads(log.request_payload)
        self.assertIn("_extra", payload)
        self.assertEqual(payload["_extra"], {"a": 1, "b": "x"})

    def test_log_exception_attaches_authenticated_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="u1", password="x")

        request = self.factory.get("/")
        request.user = user

        log = log_exception(Exception("Boom"), request=request)
        self.assertIsNotNone(log)

        log = ExceptionLog.objects.get(pk=log.pk)
        self.assertEqual(log.user, user)

