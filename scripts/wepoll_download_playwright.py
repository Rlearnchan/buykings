#!/usr/bin/env python3
"""Download Wepoll raw posts via the special mypage data export UI."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_URL = "https://wepoll.kr/g2/bbs/mypage_data.php"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-url", default=DEFAULT_URL)
    parser.add_argument("--period-label", default="최근 3일", help="Visible period option label")
    parser.add_argument("--board-label", default="경제", help="Board radio label")
    parser.add_argument("--include-label", default="글만", help="Include-scope radio label")
    parser.add_argument("--format-label", default="CSV", help="Output format radio label")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory to save the downloaded file")
    parser.add_argument("--storage-state", type=Path, help="Playwright storage state JSON file")
    parser.add_argument("--user-data-dir", type=Path, help="Persistent browser profile directory")
    parser.add_argument("--headed", action="store_true", help="Run with a visible browser window")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--save-storage-state", type=Path, help="Write storage state after a successful run")
    parser.add_argument("--screenshot", type=Path, help="Optional screenshot path after filling the form")
    return parser


def first_visible(*locators):
    for locator in locators:
        if locator.count() and locator.first.is_visible():
            return locator.first
    raise RuntimeError("No visible locator matched")


def ensure_logged_in(page) -> None:
    if "login" in page.url:
        raise SystemExit(f"Wepoll session is not authenticated: {page.url}")
    login_warning = page.get_by_text("로그인 하십시오.", exact=True)
    if login_warning.count():
        raise SystemExit("Wepoll session is not authenticated: login warning is visible")


def open_context(playwright, args):
    chromium = playwright.chromium
    if args.user_data_dir:
        args.user_data_dir.mkdir(parents=True, exist_ok=True)
        context = chromium.launch_persistent_context(
            user_data_dir=str(args.user_data_dir),
            headless=not args.headed,
            accept_downloads=True,
        )
        page = context.pages[0] if context.pages else context.new_page()
        return context, page

    browser = chromium.launch(headless=not args.headed)
    context = browser.new_context(
        accept_downloads=True,
        storage_state=str(args.storage_state) if args.storage_state else None,
    )
    page = context.new_page()
    return context, page


def main() -> None:
    args = build_parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.storage_state and args.user_data_dir:
        raise SystemExit("Use either --storage-state or --user-data-dir, not both.")

    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        context, page = open_context(playwright, args)
        try:
            page.goto(args.page_url, wait_until="networkidle", timeout=args.timeout_ms)
            ensure_logged_in(page)

            period_button = first_visible(
                page.get_by_role("button", name=re.compile(r"최근|오늘|이번|지난|기간")),
                page.locator("[role='button']").filter(has_text=re.compile(r"최근|오늘|이번|지난|기간")),
            )
            period_button.click()
            first_visible(
                page.get_by_text(args.period_label, exact=True),
                page.locator("[role='menuitem']").filter(has_text=args.period_label),
            ).click()

            page.get_by_role("radio", name=args.board_label).check()
            page.get_by_role("radio", name=args.include_label).check()
            page.get_by_role("radio", name=args.format_label).check()

            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(args.screenshot), full_page=True)

            with page.expect_download(timeout=args.timeout_ms) as download_info:
                page.get_by_role("button", name=re.compile("다운로드")).click()
            download = download_info.value

            filename = download.suggested_filename
            destination = args.output_dir / filename
            download.save_as(str(destination))

            if args.save_storage_state:
                args.save_storage_state.parent.mkdir(parents=True, exist_ok=True)
                context.storage_state(path=str(args.save_storage_state))

            print(
                json.dumps(
                    {
                        "ok": True,
                        "page_url": page.url,
                        "period_label": args.period_label,
                        "board_label": args.board_label,
                        "include_label": args.include_label,
                        "format_label": args.format_label,
                        "downloaded_file": str(destination.resolve()),
                        "suggested_filename": filename,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        except PlaywrightTimeoutError as exc:
            raise SystemExit(f"Playwright timed out while automating Wepoll: {exc}") from exc
        finally:
            context.close()


if __name__ == "__main__":
    main()
