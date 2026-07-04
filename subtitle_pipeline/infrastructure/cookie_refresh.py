"""Tu dong lay cookie tuoi cho YouTube/Douyin bang Playwright (trinh duyet
that chay ngam) - thay the viec nguoi dung phai tu cai extension va export
cookie thu cong (xem HANDOFF.md). Ghi ra file Netscape cookies.txt ma
`YTDLP_COOKIES_FILE` (subtitle_pipeline/infrastructure/downloader_ytdlp.py)
doc truc tiep duoc.

2 CHE DO, vi sao tach rieng:
- `setup_login_session()`: mo trinh duyet THAT (khong an), nguoi dung tu
  dang nhap YouTube/Douyin 1 LAN DUY NHAT trong do - CAN cho nguoi that
  thao tac (giai CAPTCHA neu co, nhap OTP...) nen KHONG the chay an/tu dong
  hoa hoan toan, va KHONG the goi tu backend API (server khong co man hinh).
  Profile (bao gom session dang nhap) duoc luu vao `profile_dir`, tai su
  dung moi lan refresh sau nay.
- `refresh_cookies()`: mo LAI dung profile da luu o tren nhung o che do AN
  (headless) - khong can dang nhap lai, chi ghe qua tung trang de lay cookie
  MOI (bao gom ca cookie JS tao ra chi co duoc khi thuc su chay JS, HTTP
  request thuong khong lam duoc - xem HANDOFF.md). Ham nay AN TOAN de goi
  tu dong (CLI dinh ky hoac nut "Lam moi cookie" trong Admin, xem
  backend/routers/admin.py).

LUU Y QUAN TRONG: neu KHONG dang nhap YouTube trong buoc setup (chi de trinh
duyet o trang chu, khong dang nhap), cookie lay duoc van la cookie AN DANH -
co the KHONG du de vuot qua kiem tra "Sign in to confirm you're not a bot"
cua YouTube tren mot so video bi gan co gioi han do tuoi/nhay cam. Nen dang
nhap that trong buoc setup neu muon YouTube on dinh nhat.

**DOUYIN VAN CHUA TAI DUOC DU CO COOKIE MOI (2026-07-05, xem HANDOFF.md):**
da xac nhan bang cach doc source code yt-dlp (`yt_dlp/extractor/tiktok.py`,
class DouyinIE._real_extract) - co dong comment `# TODO: Run verification
challenge code to generate signature cookies` ngay truoc loi "Fresh cookies
(not necessarily logged in) are needed". Day la GIOI HAN CUA YT-DLP (chua
code xong buoc giai verification challenge cua Douyin), KHONG PHAI do cookie
cu/thieu - da thu voi 44 cookie that (gom passport_csrf_token, ttwid,
odin_tt...) van loi y het. Van giu Douyin trong DEFAULT_SITES vi khong hai
gi (cookie co san neu yt-dlp sua xong trong tuong lai), nhung dung ky vong
no lam Douyin tai duoc ngay bay gio.
"""

import os
import sys
import time
from pathlib import Path

DEFAULT_SITES = {
    "youtube": "https://www.youtube.com/",
    "douyin": "https://www.douyin.com/",
}

DEFAULT_PROFILE_DIR = Path("storage/browser_profile")
DEFAULT_COOKIES_PATH = Path("cookies.txt")

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _cookie_to_netscape_line(cookie: dict) -> str:
    """1 cookie tu `BrowserContext.cookies()` (dict: name/value/domain/path/
    expires/secure...) -> 1 dong dinh dang Netscape ma yt-dlp `--cookies`
    doc duoc. Cookie phien (session, `expires=-1` hoac None trong Playwright)
    duoc gia han 1 nam thay vi ghi -1 - Netscape/yt-dlp coi gia tri am la da
    het han va se bo qua cookie do.
    """
    domain = cookie["domain"]
    include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"

    expiry = cookie.get("expires")
    if expiry is None or expiry < 0:
        expiry = int(time.time()) + 365 * 24 * 3600
    secure = "TRUE" if cookie.get("secure") else "FALSE"

    return "\t".join(
        [
            domain,
            include_subdomains,
            cookie.get("path", "/"),
            secure,
            str(int(expiry)),
            cookie["name"],
            cookie["value"],
        ]
    )


def _write_netscape_file(cookies: list[dict], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Netscape HTTP Cookie File",
        "# Sinh tu dong boi cookie_refresh.py - dung sua tay, chay lai script de cap nhat.",
    ]
    lines += [_cookie_to_netscape_line(c) for c in cookies]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(cookies)


def setup_login_session(
    profile_dir: Path = DEFAULT_PROFILE_DIR, sites: dict[str, str] | None = None
) -> None:
    """Chay 1 LAN DUY NHAT tu terminal (`python -m
    subtitle_pipeline.infrastructure.cookie_refresh --setup`) - mo Chromium
    THAT de nguoi dung tu dang nhap YouTube/Douyin, roi nhan Enter trong
    terminal de luu profile va dong trinh duyet.
    """
    from playwright.sync_api import sync_playwright

    sites = sites or DEFAULT_SITES
    profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile_dir), headless=False, user_agent=_USER_AGENT
        )
        page = context.new_page()
        for url in sites.values():
            page.goto(url, wait_until="load", timeout=30_000)

        print(
            "Da mo trinh duyet - dang nhap YouTube/Douyin (neu muon) trong "
            "cua so vua mo, roi quay lai day.",
            file=sys.stderr,
        )
        input("Nhan Enter sau khi dang nhap xong (hoac bo qua neu chi can cookie an danh)...")
        context.close()


def refresh_cookies(
    output_path: Path = DEFAULT_COOKIES_PATH,
    profile_dir: Path = DEFAULT_PROFILE_DIR,
    sites: dict[str, str] | None = None,
    wait_seconds: float = 2.0,
) -> int:
    """Dung lai profile da dang nhap (`setup_login_session`) de lay cookie
    MOI, chay AN (headless) - khong can dang nhap lai. An toan de goi tu
    dong dinh ky hoac tu 1 endpoint backend. Tra ve so cookie lay duoc.
    """
    from playwright.sync_api import sync_playwright

    sites = sites or DEFAULT_SITES
    profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile_dir), headless=True, user_agent=_USER_AGENT
        )
        page = context.new_page()
        for url in sites.values():
            page.goto(url, wait_until="load", timeout=30_000)
            page.wait_for_timeout(int(wait_seconds * 1000))
        cookies = context.cookies()
        context.close()

    return _write_netscape_file(cookies, output_path)


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--setup", action="store_true", help="Mo trinh duyet that de dang nhap 1 lan")
    mode.add_argument(
        "--refresh", action="store_true", help="Chay an, lay cookie moi tu profile da luu"
    )
    args = parser.parse_args()

    cookies_path = Path(os.environ.get("YTDLP_COOKIES_FILE", str(DEFAULT_COOKIES_PATH)))

    if args.setup:
        setup_login_session()
        print(f"Da luu profile vao {DEFAULT_PROFILE_DIR}.")
    else:
        count = refresh_cookies(output_path=cookies_path)
        print(f"Da ghi {count} cookie vao {cookies_path}.")


if __name__ == "__main__":
    _main()
