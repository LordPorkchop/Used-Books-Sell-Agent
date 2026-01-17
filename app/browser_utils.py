from playwright.sync_api import sync_playwright, Browser, BrowserContext
from typing import Literal


def start_playwright(
    browsertype: Literal["chromium", "firefox", "webkit"] = "chromium",
    use_obfuscation_headers: bool = True,
) -> tuple[Browser, BrowserContext]:
    """Starts playwright browser and returns browser as well as context

    Args:
        browsertype (Literal["chromium", "firefox", "webkit"], optional): Which browser type to use. Defaults to "chromium".
        use_obfuscation_headers (bool, optional): Whether to use obfuscated headers (tricks most bot detection). Defaults to True.

    Raises:
        ValueError: If the passed browser type is invalid

    Returns:
        tuple[Browser, BrowserContext]: The created browser along with the created context
    """
    p = sync_playwright().start()
    match browsertype:
        case "chromium":
            browser = p.chromium.launch()
        case "firefox":
            browser = p.firefox.launch()
        case "webkit":
            browser = p.webkit.launch()
        case _:
            raise ValueError('Invalid browser type "{}"'.format(browsertype))

    if use_obfuscation_headers:
        context = browser.new_context(
            locale="de-DE",
            timezone_id="Europe/Berlin",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept-Language": "de-DE,de;q=0.9",
            },
        )
    else:
        context = browser.new_context()

    return browser, context


def stop_playwright(browser: Browser):
    """Stops playwright browser instance

    Args:
        browser (Browser): Browser instance to close

    Raises:
        ValueError: If browser cannot be closed
    """
    try:
        browser.close()
    except Exception:
        raise ValueError('"{}" cannot be closed since it is not open'.format(browser))
