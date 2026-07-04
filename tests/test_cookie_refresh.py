"""Test _cookie_to_netscape_line/_write_netscape_file - ham thuan, khong can
Playwright/trinh duyet that.
"""

import time

from subtitle_pipeline.infrastructure.cookie_refresh import (
    _cookie_to_netscape_line,
    _write_netscape_file,
)


def test_domain_with_leading_dot_marks_include_subdomains_true():
    cookie = {
        "name": "ttwid",
        "value": "abc123",
        "domain": ".douyin.com",
        "path": "/",
        "secure": True,
        "expires": time.time() + 3600,
    }

    line = _cookie_to_netscape_line(cookie)

    fields = line.split("\t")
    assert fields[0] == ".douyin.com"
    assert fields[1] == "TRUE"
    assert fields[3] == "TRUE"  # secure
    assert fields[5] == "ttwid"
    assert fields[6] == "abc123"


def test_domain_without_leading_dot_marks_include_subdomains_false():
    cookie = {
        "name": "x",
        "value": "y",
        "domain": "www.youtube.com",
        "path": "/",
        "secure": False,
        "expires": time.time() + 3600,
    }

    fields = _cookie_to_netscape_line(cookie).split("\t")

    assert fields[0] == "www.youtube.com"
    assert fields[1] == "FALSE"
    assert fields[3] == "FALSE"


def test_session_cookie_expiry_extended_instead_of_negative():
    # Playwright tra ve expires=-1 (hoac None) cho cookie phien - Netscape/
    # yt-dlp coi gia tri am la da het han va bo qua, nen phai gia han.
    cookie = {
        "name": "sess",
        "value": "z",
        "domain": "youtube.com",
        "path": "/",
        "secure": True,
        "expires": -1,
    }

    fields = _cookie_to_netscape_line(cookie).split("\t")

    assert int(fields[4]) > time.time()


def test_write_netscape_file_has_required_header_and_returns_count(tmp_path):
    cookies = [
        {"name": "a", "value": "1", "domain": "youtube.com", "path": "/", "expires": -1},
        {"name": "b", "value": "2", "domain": ".douyin.com", "path": "/", "expires": -1},
    ]
    output_path = tmp_path / "cookies.txt"

    count = _write_netscape_file(cookies, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert count == 2
    assert content.startswith("# Netscape HTTP Cookie File")
    assert "youtube.com" in content
    assert ".douyin.com" in content
