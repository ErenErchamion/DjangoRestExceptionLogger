import json

from django.test import SimpleTestCase, RequestFactory
from django.utils.datastructures import MultiValueDict

from django_rest_exception_logger.utils import (
    extract_payload_for_logging,
    querydict_to_dict,
    safe_json_dumps,
    summarize_files,
)


class RequestDataUtilsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_querydict_to_dict_handles_multivaluedict(self):
        qd = MultiValueDict({"a": ["1", "2"], "b": ["x"]})
        self.assertEqual(querydict_to_dict(qd), {"a": ["1", "2"], "b": ["x"]})

    def test_safe_json_dumps_falls_back_to_str(self):
        class X:
            def __str__(self):
                return "X()"

        s = safe_json_dumps({"x": X()})
        obj = json.loads(s)
        self.assertEqual(obj["x"], "X()")

    def test_extract_payload_for_logging_unknown_binary(self):
        request = self.factory.generic(
            "POST",
            "/bin/",
            data=b"\x00\xff\x01\x02" * 10,
            content_type="application/octet-stream",
        )
        # mimic middleware caching
        request.request_body = request.body

        payload = extract_payload_for_logging(request)
        self.assertEqual(payload["content_type"], "application/octet-stream")
        self.assertIn("body_preview", payload)
        self.assertIn("body_length", payload)

    def test_summarize_files_empty(self):
        self.assertEqual(summarize_files({}), {})

