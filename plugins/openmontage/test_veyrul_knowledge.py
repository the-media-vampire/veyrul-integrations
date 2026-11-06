"""Run with the OpenMontage tools package on PYTHONPATH. Network stays on loopback."""
import http.server
import json
import threading
import time
import unittest
from unittest.mock import patch

import veyrul_knowledge as plugin
from tools.tool_registry import ToolRegistry


CONTEXT = {"schema": "context/v1", "records": [{
    "id": "test_fixture", "title": "Fixture only", "url": "https://example.invalid/record",
    "content": "Untrusted sample text", "revision": 1, "resources": [],
}], "guidance": "Fixture, not live knowledge", "truncated": False}


class Handler(http.server.BaseHTTPRequestHandler):
    requests = []
    status = 200
    content_type = "application/json"
    body = json.dumps(CONTEXT).encode()
    delay = 0

    def log_message(self, *args):
        pass

    def do_GET(self):
        type(self).requests.append({"path": self.path, "headers": dict(self.headers)})
        if self.delay:
            time.sleep(self.delay)
        self.send_response(self.status)
        self.send_header("Content-Type", self.content_type)
        if self.status == 302:
            self.send_header("Location", "http://127.0.0.1:%s/redirected" % self.server.server_port)
        self.end_headers()
        try:
            self.wfile.write(self.body)
        except (BrokenPipeError, ConnectionResetError):
            pass


class ToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        Handler.requests = []
        Handler.status = 200
        Handler.body = json.dumps(CONTEXT).encode()
        Handler.content_type = "application/json"
        Handler.delay = 0
        self.endpoint = patch.object(plugin, "ENDPOINT", "http://127.0.0.1:%s/v1/context" % self.server.server_port)
        self.endpoint.start()
        self.addCleanup(self.endpoint.stop)
        self.tool = plugin.VeyrulKnowledgeTool()
        self.query = {"query": "caption timing & speed", "share_query": True}

    def test_native_registration_and_capability_without_network(self):
        with patch.object(plugin.urllib.request, "build_opener", side_effect=AssertionError("network")):
            registry = ToolRegistry()
            self.assertEqual(registry.register_module(plugin), ["veyrul_knowledge"])
            self.assertEqual(registry.get_by_capability("media_knowledge"), [registry.get("veyrul_knowledge")])
            self.assertEqual(registry.network_required_tools(), ["veyrul_knowledge"])
            info = registry.get("veyrul_knowledge").get_info()
            self.assertEqual(info["runtime"], "api")
            self.assertEqual(info["status"], "available")

    def test_context_preserved_and_minimal_request(self):
        result = self.tool.execute(self.query)
        self.assertTrue(result.success)
        self.assertEqual(result.data["context"], CONTEXT)
        self.assertEqual(result.artifacts, [])
        self.assertEqual(len(Handler.requests), 1)
        request = Handler.requests[0]
        self.assertEqual(request["path"], "/v1/context?q=caption+timing+%26+speed&limit=3&detail=compact")
        self.assertNotIn("Authorization", request["headers"])
        self.assertNotIn("Cookie", request["headers"])

    def test_rejects_private_extras_and_invalid_inputs_before_network(self):
        cases = [None, {}, dict(self.query, transcript="PRIVATE"), dict(self.query, project_dir="PRIVATE"),
                 dict(self.query, share_query=False), dict(self.query, share_query=1),
                 dict(self.query, limit=True), dict(self.query, limit=0), dict(self.query, limit=6),
                 dict(self.query, query="x"), dict(self.query, query="x" * 301),
                 dict(self.query, query="a\nb"), dict(self.query, query=["x"])]
        for value in cases:
            with self.subTest(value=value):
                self.assertFalse(self.tool.execute(value).success)
        self.assertEqual(Handler.requests, [])

    def test_dry_run_has_no_network(self):
        result = self.tool.dry_run(self.query)
        self.assertTrue(result["would_execute"])
        self.assertFalse(result["network_performed"])
        self.assertFalse(self.tool.dry_run({})["would_execute"])
        self.assertEqual(Handler.requests, [])

    def test_redirect_is_not_followed(self):
        Handler.status = 302
        self.assertFalse(self.tool.execute(self.query).success)
        self.assertEqual(len(Handler.requests), 1)

    def test_rate_limit_has_no_retry_and_no_error_body_leak(self):
        Handler.status = 429
        Handler.body = b"PRIVATE ERROR PAYLOAD"
        result = self.tool.execute(self.query)
        self.assertFalse(result.success)
        self.assertIn("429", result.error)
        self.assertNotIn("PRIVATE", result.error)
        self.assertEqual(len(Handler.requests), 1)

    def test_timeout_is_bounded_no_retry(self):
        Handler.delay = 0.1
        with patch.object(plugin, "TIMEOUT_SECONDS", 0.02):
            self.assertFalse(self.tool.execute(self.query).success)
        self.assertEqual(len(Handler.requests), 1)

    def test_invalid_response_fails_cleanly(self):
        cases = [b"not JSON", b"[]", b'{"schema":"other"}', b"x" * (plugin.MAX_BYTES + 1),
                 json.dumps(dict(CONTEXT, records=[None])).encode(),
                 json.dumps(dict(CONTEXT, records=CONTEXT["records"] * 11)).encode()]
        for value in cases:
            with self.subTest(bytes=len(value)):
                Handler.body = value
                self.assertFalse(self.tool.execute(self.query).success)

    def test_wrong_content_type(self):
        Handler.content_type = "text/html"
        self.assertFalse(self.tool.execute(self.query).success)

    def test_empty_results_are_explicit_success(self):
        Handler.body = json.dumps(dict(CONTEXT, records=[])).encode()
        result = self.tool.execute(self.query)
        self.assertTrue(result.success)
        self.assertEqual(result.data["context"]["records"], [])


if __name__ == "__main__":
    unittest.main()
