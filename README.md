# Shopping API Lab: beginner starter code

Build a public, read-only product API with fake data, then connect a frontend running on your laptop. This starter accompanies API Gateway Part 2.

## What you will build

| Shopper action | HTTP API route | Python request handler | Expected result |
| --- | --- | --- | --- |
| Search for headphones | `GET /products?q=headphones` | `search_products` | `200` with two matching products |
| Open a product | `GET /products/1738` | `get_product` | `200` with Everyday Headphones, USD 79.99 |
| Open a missing product | `GET /products/9999` | `get_product` | `404` with a useful message |
| Supply a malformed product ID | `GET /products/abc` | `get_product` | `400` with a useful message |

The route key is `GET /products`, without the query string. The detail route's template is `GET /products/{productId}`. API Gateway supplies the actual path parameter, such as `1738`, in its Lambda event.

Two logical request handlers share **one Lambda function** to keep this project small. `handler` is the Lambda entry point; it dispatches to `search_products` or `get_product` using `event['routeKey']`. You can split these handlers into separate functions later. An API does not require one Lambda function per route.

The sample uses an in-memory Python dictionary, **not a deployed database**. There are no order-history or sign-in routes. Keep this initial catalog public and fake. Implement and test authentication plus ownership checks before adding personal data.

## Files

- `src/app.py`: Lambda code, using only the Python standard library.
- `template.yaml`: AWS SAM infrastructure template.
- `frontend/index.html`: local search and product-detail UI, with no build tools.
- `tests/test_app.py`: offline tests of the handler's behavior and logging.
- `events/`: HTTP API payload-format 2.0 examples for local invocation.

## Check your AWS environment before deploying

In the new AWS experience, first verify your assigned Region, the services and operations available to your account, and the permissions of your current development identity. This starter creates API Gateway, Lambda, CloudWatch Logs, and an IAM execution role through CloudFormation; SAM also needs a deployment artifact bucket. API Gateway service availability alone does not prove you can perform every deployment step.

Use your approved AWS sign-in flow and a named development profile. Ask your coding assistant with Agent Toolkit for AWS to explain the template and check your account's available services and permissions before making changes. Agent Toolkit is a development aid; it is not part of the API's runtime request path. Do not paste credentials into the frontend or source code.

There is no promise that deployment is free or qualifies for an activity reward. Review the account's usage controls and applicable charges. The small throttle setting is a teaching control, not a spending cap.

## Run tests without an AWS account

From this `code` directory, with Python 3.12:

```bash
python3 -m unittest discover -s tests -v
```

These tests need no packages or AWS credentials. They cover product detail, search, empty results, malformed IDs, missing products, unsupported routes, payload version, and omission of sensitive request fields from logs.

## Optional: build and deploy the AWS resources

Prerequisites: Python 3.12, a current AWS SAM CLI, AWS CLI, an authenticated development profile, and permissions for this template. Docker is only needed if you choose SAM's container-based local execution or build options.

Choose your own assigned Region and existing profile:

```bash
DEMO_PROFILE='your-development-profile'
DEMO_REGION='your-assigned-region'
aws sts get-caller-identity --profile "$DEMO_PROFILE" --region "$DEMO_REGION"
sam validate --lint --region "$DEMO_REGION"
sam build
sam deploy --guided --stack-name beginner-product-api \
  --profile "$DEMO_PROFILE" --region "$DEMO_REGION" \
  --capabilities CAPABILITY_IAM
```

Review the resources before confirming deployment. The catalog routes intentionally have no authorizer and are publicly callable. The IAM role created by this template only lets Lambda create streams and write events in its designated log group. CloudFormation's deployment permissions are separate from that runtime role. HTTP API log delivery also needs the appropriate CloudWatch Logs setup permissions for the deploying identity.

## Test the deployed endpoint

Copy `ApiBaseUrl` from the stack outputs:

```bash
DEMO_API_BASE='https://your-api-id.execute-api.your-region.amazonaws.com'
curl -i "$DEMO_API_BASE/products?q=headphones"
curl -i "$DEMO_API_BASE/products/1738"
curl -i "$DEMO_API_BASE/products/9999"
curl -i "$DEMO_API_BASE/products/abc"
```

The `$default` stage is served from the base URL, so do not add `/prod` or `/$default`. An unknown route is normally rejected by API Gateway before Lambda runs. The code's unknown-route branch is also useful when testing the function directly.

## Connect the local frontend

From the same `code` directory:

```bash
python3 -m http.server 3000 --bind 127.0.0.1 --directory frontend
```

Open `http://localhost:3000`, enter `ApiBaseUrl`, and search for `headphones`. Click **View product 1738**. The page displays the URL, status, and JSON response.

Use `localhost`, not `127.0.0.1`, in the browser's address bar: those are different CORS origins. The template permits exactly `http://localhost:3000` and the `GET` method. CORS controls browser access to responses; it does not authenticate callers or block a terminal client. Serve the page through this local web server instead of opening it as a `file://` document.

## Find the request in the logs

1. Open the log group named by the `ApiAccessLogGroup` stack output.
2. Find a record for `GET /products/{productId}` with status `200` or `404`.
3. Copy its `requestId`.
4. Search the log group named by `FunctionLogGroup` for that same ID.

Gateway access logs record the gateway's view of the request. The function's JSON log line records which logical route ran and the status it returned. Neither includes authorization headers, request bodies, or search text. The access-log format intentionally omits free-form integration error text so embedded quotes cannot invalidate its JSON. For deeper diagnosis, inspect the function logs and Gateway metrics; if you add error text, account for escaping in your chosen log format. Restrict log access.

## AWS configuration choices

| Setting | Starter choice | Why it is here |
| --- | --- | --- |
| API type | HTTP API | A small request-response API with Lambda integrations |
| Integration payload | `2.0` | Matches `routeKey`, `pathParameters`, and `requestContext` in the Python code |
| Stage | `$default` | Keeps the invoke URL simple; SAM creates an automatically deployed HTTP API stage |
| Authorizer | None | Only fake, public catalog data is served |
| CORS | `http://localhost:3000`; `GET` | Lets the local browser frontend read the API response |
| Throttle rate / burst | 5 requests/second / 10 requests | Small illustrative per-route defaults; best-effort targets, not strict ceilings or a bill cap |
| Lambda runtime | Python 3.12 | Supported runtime verified against AWS documentation on 2026-10-09 |
| Lambda timeout | 5 seconds | More than this in-memory example needs; does not make long jobs safe |
| Lambda permissions | Write to its one log group | No database or broad AWS permissions are needed |
| Log retention | 7 days | Limits how long demo log records remain |

The supplied code does not simulate AWS throttling, authorizers, or managed metrics locally. Check those after deployment. Both routes use the same stage defaults; this is not an application-wide concurrency guarantee.

## Suggested next challenge

Ask your coding assistant with Agent Toolkit for AWS to explain one request end to end, then replace the fake dictionary with a database lookup. Review required account support and narrowly scoped permissions first. After that, add a protected order-history route and test two different users, verifying that each sees only their own orders.

## Clean up

When finished with your own deployed demo:

```bash
sam delete --stack-name beginner-product-api \
  --profile "$DEMO_PROFILE" --region "$DEMO_REGION"
```

Confirm the stack name and account before deleting. This template has no retention policies, so stack deletion removes its API, Lambda function, execution role, and two log groups. Review any SAM deployment artifacts and any resources you added manually. Stop the local server with Ctrl+C.

## Validation status

The handler's offline tests were run while preparing this package. No AWS resources were deployed, and no live API, CORS, IAM, log delivery, or account eligibility was verified. See `validation.txt` for the exact local checks performed.
