"""Bounded HTTP requests, no automatic POST retries (delivery queue owns retries)."""

import json
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError


class HTTPFailure(Exception):
    def __init__(self, status, body):
        self.status, self.body = status, body
        super().__init__(f"HTTP status {status}")


def request_json(url, payload=None, proxy=None, timeout=20):
    # Explicitly disable implicit environment proxies unless configured.
    opener = build_opener(
        ProxyHandler({"http": proxy, "https": proxy} if proxy else {})
    )
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"User-Agent": "flats-bot/2", "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(
        url,
        data=data,
        headers=headers,
    )
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(8 * 1024 * 1024 + 1)
            if len(body) > 8 * 1024 * 1024:
                raise ValueError("HTTP response exceeds 8 MiB")
    except HTTPError as exc:
        body = exc.read(65536)
        try:
            body = json.loads(body)
        except (ValueError, UnicodeError):
            body = {}
        raise HTTPFailure(exc.code, body) from None
    return json.loads(body)
