from __future__ import annotations

import json

import pytest

from sourcesight import data_requests


class FakeResponse:
    def __init__(self, body: bytes, url: str):
        self.body = body
        self.url = url
        self.headers = {"Content-Length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def geturl(self):
        return self.url

    def read(self, size=-1):
        body, self.body = self.body, b""
        return body


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def open(self, request, timeout):
        self.calls += 1
        assert timeout == data_requests.TIMEOUT_SECONDS
        return self.response


def test_download_writes_source_attribution_and_reuses_fresh_cache(tmp_path, monkeypatch):
    record = data_requests.SOURCES["opensanctions"][0]
    opener = FakeOpener(FakeResponse(b"id,name\n1,Example\n", record["url"]))
    monkeypatch.setattr(data_requests, "build_opener", lambda handler: opener)

    path, cached = data_requests._download(record, tmp_path)
    metadata = json.loads(data_requests._metadata_path(path).read_text(encoding="utf-8"))
    assert path.read_bytes() == b"id,name\n1,Example\n"
    assert metadata["publisher"] == "OpenSanctions"
    assert metadata["source_url"] == record["url"]
    assert cached is False

    same_path, cached = data_requests._download(record, tmp_path)
    assert same_path == path
    assert cached is True
    assert opener.calls == 1


def test_download_rejects_oversized_response_without_publishing_file(tmp_path, monkeypatch):
    record = data_requests.SOURCES["dol_goods"][0]
    monkeypatch.setattr(data_requests, "MAX_RESPONSE_BYTES", 3)
    monkeypatch.setattr(
        data_requests, "build_opener",
        lambda handler: FakeOpener(FakeResponse(b"large", record["url"])),
    )

    with pytest.raises(ValueError, match="configured 3 bytes limit"):
        data_requests._download(record, tmp_path)
    assert not (tmp_path / record["filename"]).exists()


def test_configured_sources_are_https_and_allowlisted():
    for records in data_requests.SOURCES.values():
        for record in records:
            from urllib.parse import urlparse
            parsed = urlparse(record["url"])
            assert parsed.scheme == "https"
            assert parsed.hostname in record["hosts"]