import json

from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile

from django_rest_exception_logger.middleware import ExceptionMiddleware
from django_rest_exception_logger.models import ExceptionLog


class ExceptionMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_process_exception(self):
        request = self.factory.get('/')
        middleware = ExceptionMiddleware(get_response=lambda r: r)

        response = middleware.process_exception(request, Exception("Test Error"))

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content.decode("utf-8"))
        self.assertIn('error_message', data)

    def test_process_exception_with_multipart_file_does_not_crash(self):
        upload = SimpleUploadedFile(
            "test.bin",
            b"\xff\xd8\xff\x00\x01\x02",  # binary-ish content
            content_type="application/octet-stream",
        )
        request = self.factory.post(
            "/upload/",
            data={"foo": "bar", "file": upload},
        )
        # Ensure middleware body capture is executed (normally happens in __call__)
        middleware = ExceptionMiddleware(get_response=lambda r: r)
        middleware.__call__(request)

        response = middleware.process_exception(request, Exception("Boom"))
        self.assertEqual(response.status_code, 500)

        log = ExceptionLog.objects.latest("id")
        self.assertIn("multipart/form-data", log.request_payload)
        self.assertIn("files", log.request_payload)
        self.assertIn("test.bin", log.request_payload)

    def test_process_exception_with_invalid_utf8_json_body_does_not_crash(self):
        # Body starts with 0xff which isn't valid UTF-8; content type says JSON.
        bad_body = b"{\"a\": 1, \"b\": \"\xff\"}"
        request = self.factory.generic(
            "POST",
            "/json/",
            data=bad_body,
            content_type="application/json",
        )
        middleware = ExceptionMiddleware(get_response=lambda r: r)
        middleware.__call__(request)

        response = middleware.process_exception(request, Exception("Boom"))
        self.assertEqual(response.status_code, 500)

        log = ExceptionLog.objects.latest("id")
        # Should have logged parse error metadata + a safe preview, not raised UnicodeDecodeError.
        self.assertIn("_parse_error", log.request_payload)
        self.assertIn("body_preview", log.request_payload)
