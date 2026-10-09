"""Fake, public product catalog for API Gateway HTTP API payload format 2.0.

Two logical request handlers share one Lambda function. No database or user data.
"""

import json
import re

PRODUCTS = {
    "1738": {"productId": "1738", "name": "Everyday Headphones", "price": 79.99, "currency": "USD"},
    "1739": {"productId": "1739", "name": "Travel Headphones", "price": 149.99, "currency": "USD"},
    "1740": {"productId": "1740", "name": "Laptop Stand", "price": 39.99, "currency": "USD"},
}


def search_products(event):
    """Read a query parameter. Missing or blank q lists all fake products."""
    query = (event.get("queryStringParameters") or {}).get("q", "")
    if not isinstance(query, str) or len(query) > 80:
        return 400, {"message": "Search q must be at most 80 characters."}
    query = query.strip().casefold()
    matches = [p for p in PRODUCTS.values() if query in p["name"].casefold()]
    return 200, {"items": matches, "count": len(matches)}


def get_product(event):
    """Read a path parameter. A real application could query a database here."""
    product_id = (event.get("pathParameters") or {}).get("productId", "")
    if not isinstance(product_id, str) or not re.fullmatch(r"[0-9]{1,12}", product_id):
        return 400, {"message": "Product ID must contain 1 to 12 digits."}
    product = PRODUCTS.get(product_id)
    if product is None:
        return 404, {"message": "Product not found."}
    return 200, product


HANDLERS = {
    "GET /products": search_products,
    "GET /products/{productId}": get_product,
}


def handler(event, context):
    """Lambda entry point; API Gateway supplies routeKey and parsed parameters."""
    route_key = event.get("routeKey", "")
    request_id = str((event.get("requestContext") or {}).get("requestId", "local"))[:160]
    if event.get("version") != "2.0":
        status, body = 400, {"message": "Expected HTTP API payload format 2.0."}
    elif route_key not in HANDLERS:
        status, body = 404, {"message": "Route not found."}
    else:
        status, body = HANDLERS[route_key](event)

    # Deliberately omit headers, tokens, request bodies and search text.
    print(json.dumps({
        "event": "catalog_request",
        "requestId": request_id,
        "routeKey": route_key if route_key in HANDLERS else "unmatched",
        "status": status,
    }))
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json", "cache-control": "no-store"},
        "body": json.dumps(body),
        "isBase64Encoded": False,
    }
