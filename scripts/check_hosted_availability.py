"""Small HTTPS/readiness monitor. No login, writes, credentials or load generation."""

import json
import os
import urllib.request
from urllib.parse import urlsplit

url = os.environ["PUBLIC_APPLICATION_URL"].rstrip("/")
parsed = urlsplit(url)
if (
    parsed.scheme != "https"
    or not parsed.hostname
    or parsed.username
    or parsed.password
):
    raise SystemExit("An HTTPS public origin without credentials is required")
if parsed.path or parsed.query or parsed.fragment:
    raise SystemExit("Use the public origin only")
for path in ("/", "/ready", "/api/auth/options"):
    request = urllib.request.Request(
        url + path, headers={"User-Agent": "PortfolioLedger-availability"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise SystemExit("Public availability check failed")
        if path == "/ready" and json.load(response).get("status") != "ready":
            raise SystemExit("Database readiness failed")
        if path == "/api/auth/options" and not json.load(response).get(
            "public_review_enabled"
        ):
            raise SystemExit("Public reviewer disabled")
    print(path + ": OK")
