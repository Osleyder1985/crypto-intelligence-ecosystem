"""Tests for byte-preserving public market capture."""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "market_selection"))

import capture_public_market_data as capture  # noqa: E402


class FakeResponse:
    status = 200

    def __init__(self, body: bytes):
        self.body = body
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        if size is None or size < 0:
            chunk = self.body[self.offset:]
            self.offset = len(self.body)
            return chunk
        chunk = self.body[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


class PublicCaptureTests(unittest.TestCase):
    def test_raw_bytes_are_hashed_and_retained_as_base64(self):
        raw = b'{"result":true,"timestamp":1792368000000,"data":{"symbols":[]}}'
        with patch.object(capture, "urlopen", return_value=FakeResponse(raw)):
            result = capture.request_capture("pionex", "https://api.pionex.com/test")
        self.assertEqual(result["capture_status"], "PASS")
        self.assertEqual(result["response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(base64.b64decode(result["response_base64"]), raw)
        self.assertEqual(result["response_bytes"], len(raw))

    def test_non_object_json_is_not_accepted_as_a_valid_capture(self):
        raw = b'[]'
        with patch.object(capture, "urlopen", return_value=FakeResponse(raw)):
            result = capture.request_capture("pionex", "https://api.pionex.com/test")
        self.assertEqual(result["capture_status"], "FAIL")
        self.assertEqual(result["error_type"], "InvalidResponseSchema")
        self.assertEqual(result["response_sha256"], hashlib.sha256(raw).hexdigest())

    def test_invalid_json_is_not_accepted(self):
        raw = b'{broken'
        with patch.object(capture, "urlopen", return_value=FakeResponse(raw)):
            result = capture.request_capture("pionex", "https://api.pionex.com/test")
        self.assertEqual(result["capture_status"], "FAIL")
        self.assertEqual(result["error_type"], "JSONDecodeError")
        self.assertEqual(result["response_sha256"], hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
