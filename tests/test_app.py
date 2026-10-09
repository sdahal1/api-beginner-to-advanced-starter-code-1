"""Offline behavior tests. These do not create AWS resources."""

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from app import handler  # noqa: E402


def event(route="GET /products/{productId}", product_id="1738", query=None):
    return {
        "version": "2.0",
        "routeKey": route,
        "requestContext": {"requestId": "test-request-123"},
        "pathParameters": {"productId": product_id},
        "queryStringParameters": query,
    }


class CatalogTests(unittest.TestCase):
    def invoke(self, request):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            response = handler(request, None)
        return response, json.loads(response["body"]), json.loads(output.getvalue())

    def test_get_exact_product_and_json_contract(self):
        response, body, log = self.invoke(event())
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body, {"productId": "1738", "name": "Everyday Headphones", "price": 79.99, "currency": "USD"})
        self.assertEqual(response["headers"]["content-type"], "application/json")
        self.assertFalse(response["isBase64Encoded"])
        self.assertEqual(log["requestId"], "test-request-123")

    def test_search_trims_and_matches_case_insensitively(self):
        response, body, _ = self.invoke(event("GET /products", query={"q": " HEADPHONES "}))
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual([p["productId"] for p in body["items"]], ["1738", "1739"])
        self.assertEqual(body["count"], 2)

    def test_search_without_query_returns_catalog(self):
        response, body, _ = self.invoke(event("GET /products"))
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["count"], 3)

    def test_no_search_matches_is_success_with_empty_list(self):
        response, body, _ = self.invoke(event("GET /products", query={"q": "coffee"}))
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body, {"items": [], "count": 0})

    def test_nonexistent_product_is_404(self):
        response, body, log = self.invoke(event(product_id="9999"))
        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(body["message"], "Product not found.")
        self.assertEqual(log["status"], 404)

    def test_invalid_ids_are_bad_requests(self):
        for product_id in ("abc", "", "1738 OR 1=1", "1" * 13, "١٧٣٨"):
            with self.subTest(product_id=product_id):
                response, _, _ = self.invoke(event(product_id=product_id))
                self.assertEqual(response["statusCode"], 400)

    def test_overlong_search_is_bad_request(self):
        response, _, _ = self.invoke(event("GET /products", query={"q": "x" * 81}))
        self.assertEqual(response["statusCode"], 400)

    def test_other_routes_do_not_execute_product_handlers(self):
        response, _, log = self.invoke(event("POST /products"))
        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(log["routeKey"], "unmatched")

    def test_logging_omits_tokens_body_and_search_query(self):
        request = event("GET /products", query={"q": "private-search"})
        request.update({"headers": {"authorization": "Bearer secret-token"}, "body": "private-body"})
        _, _, log = self.invoke(request)
        self.assertEqual(set(log), {"event", "requestId", "routeKey", "status"})
        self.assertNotIn("private", json.dumps(log))
        self.assertNotIn("secret", json.dumps(log))

    def test_non_v2_event_reports_configuration_mismatch(self):
        request = event()
        request["version"] = "1.0"
        response, body, _ = self.invoke(request)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("2.0", body["message"])


if __name__ == "__main__":
    unittest.main()
