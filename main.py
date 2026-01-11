import logging
import os

from flask import Flask
from logging.config import dictConfig
from playwright.sync_api import sync_playwright, TimeoutError, Browser, BrowserContext
from typing import Literal


def start_playwright(
    browsertype: Literal["chromium", "firefox", "webkit"] = "chromium",
    use_obfuscation_headers: bool = True,
) -> tuple[Browser, BrowserContext]:
    """Starts playwright browser and returns browser as well as context

    Args:
        browsertype (Literal[&quot;chromium&quot;, &quot;firefox&quot;, &quot;webkit&quot;], optional): Which browser type to use. Defaults to "chromium".
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
    try:
        browser.close()
    except Exception:
        raise ValueError('"{}" cannot be closed since it is not open'.format(browser))


def rebuy(context: BrowserContext, isbn: str) -> float:
    if not isbn.isdigit() or len(isbn) not in [10, 12, 13, 15, 16]:
        raise ValueError("Invalid ISBN")

    page = context.new_page()

    logging.info("Opened new tab")

    try:
        page.goto(
            "https://www.rebuy.de/verkaufen/buecher",
            referer="/verkaufen",
            wait_until="domcontentloaded",
            timeout=5000,
        )
        logging.info("Opened Rebuy merchant page")
    except TimeoutError:
        logging.error('"https://www.rebuy.de/verkaufen/buecher" timed out after 5s')
        page.close()
        logging.info("Closed browser page")
        return -1

    try:
        isbn_input = page.locator(
            'input[id="s_input5"], input[class*="search-input"]'
        ).first
        isbn_input.wait_for(state="visible")
        logging.info("Found ISBN input")
        isbn_input.fill(isbn)
        logging.info(f"Filled ISBN: {isbn}")
        isbn_input.press("Enter")
        logging.info("Pressed Enter to search")
        page.wait_for_load_state("domcontentloaded")
        logging.info("Search results loaded")
    except TimeoutError:
        logging.error("Failed to locate or fill ISBN input")
        page.close()
        logging.info("Closed browser page")
        return -1

    try:
        price_offer_element = page.locator('div[data-cy="product-price"]').first
        price_offer_element.wait_for(state="visible", timeout=2000)
        price_offer_text = price_offer_element.inner_text()
        price_offer = float(price_offer_text.replace("€", "").replace(",", ".").strip())
        logging.info(f"Offer price: {price_offer} EUR")
        return price_offer
    except TimeoutError:
        logging.info("No offer available for this book")
        page.close()
        logging.info("Closed browser page")
        return -1


def momox(context: BrowserContext, isbn: str) -> float:
    if not isbn.isdigit() or len(isbn) not in [10, 12, 13, 15, 16]:
        raise ValueError("Invalid ISBN")

    page = context.new_page()

    logging.info("Opened new tab")

    try:
        page.goto(
            "https://www.momox.de/buecher-verkaufen",
            referer="/",
            wait_until="domcontentloaded",
            timeout=5000,
        )
        logging.info("Opened Momox merchant page")
    except TimeoutError:
        page.close()
        logging.info("Closed browser page")
        return -1

    try:
        isbn_input = page.locator(
            'input[class*="product-input"], input[class*="searchbox-input"]'
        ).first
        isbn_input.wait_for(state="visible", timeout=2000)
    except TimeoutError:
        logging.error("Failed to locate ISBN input")
        page.close()
        logging.info("Closed browser page")
        return -1
    else:
        logging.info("Found ISBN input")

    try:
        isbn_input.fill(isbn)
        logging.info(f"Filled ISBN: {isbn}")
        isbn_input.press("Enter", timeout=2000)
    except TimeoutError:
        logging.error("Failed to fill or submit ISBN input")
        page.close()
        logging.info("Closed browser")
        return -1

    page.wait_for_load_state("domcontentloaded")
    logging.info("Search results loaded")

    try:
        price_offer_element = page.locator(".searchresult-price").first
        price_offer_element.wait_for(state="visible", timeout=1000)
        price_offer_text = price_offer_element.inner_text()
        price_offer = float(price_offer_text.replace("€", "").replace(",", ".").strip())
        logging.info(f"Offer price: {price_offer} EUR")
        page.close()
        logging.info("Closed browser page")
        logging.info(f'momox(isbn="{isbn}") -> {price_offer}')
        return price_offer
    except TimeoutError:
        logging.info("No offer available for this book")
        page.close()
        logging.info("Closed browser page")
        logging.info(f'momox(isbn="{isbn}") -> {-1}')

    return -1


def buchmaxe(context: BrowserContext, isbn: str) -> float:
    if not isbn.isdigit() or len(isbn) not in [10, 12, 13, 15, 16]:
        raise ValueError("Invalid ISBN")

    page = context.new_page()

    try:
        page.goto("https://www.buchmaxe.at")
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except TimeoutError:
        logging.error("buchmaxe.at timed out after 5000ms")
        page.close()
        logging.info("Page closed")
        return -1

    isbn_input = page.locator("input[name*=isbn_eingabe]")
    try:
        isbn_input.wait_for(state="visible", timeout=1000)
        isbn_input.fill(isbn)
        isbn_input.press("Enter", timeout=2000)
    except TimeoutError:
        logging.error("Failed to locate or fill ISBN input")
        page.close()
        return -1

    page.wait_for_load_state("domcontentloaded")

    price_offer_element = page.locator(
        "#ctl00_ctl00_plcTopvisual_updatePanel1 > div.card.text-center > div.card-body > p:nth-child(2) > span"
    )
    try:
        price_offer_element.wait_for(state="visible", timeout=2000)
        price_offer = price_offer_element.inner_text()
        price_offer = float(price_offer.replace(" €", "").replace(",", "."))
    except TimeoutError:
        logging.info("No offer available for this book")
        page.close()
        return -1
    else:
        page.close()
        if price_offer == 0:
            logging.info("No offer available for this book")
            return -1
        else:
            return price_offer


# Colored logs
class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[37m",  # Gray
        "INFO": "\033[34m",  # Blue
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord):
        log_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


# Configure logging with dictConfig
dictConfig(
    {
        "version": 1,
        "filters": {
            "info_and_warning": {
                "()": lambda: type(
                    "",
                    (object,),
                    {
                        "filter": lambda self, record: record.levelno
                        < 40  # < ERROR (40)
                    },
                )(),
            },
            "error_and_critical": {
                "()": lambda: type(
                    "",
                    (object,),
                    {
                        "filter": lambda self, record: record.levelno
                        >= 40  # >= ERROR (40)
                    },
                )(),
            },
        },
        "formatters": {
            "colored": {
                "()": ColoredFormatter,
                "format": "[%(asctime)s.%(msecs)03d] [%(levelname)-8s] [%(name)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "colored",
                "filters": ["info_and_warning"],
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "colored",
                "filters": ["error_and_critical"],
            },
        },
        "root": {"level": "INFO", "handlers": ["stdout", "stderr"]},
    }
)


app = Flask("Booksell-backend")
browser, context = start_playwright()


@app.route("/")
def showHelp():
    return {
        "help": {"commands": ["/momox/<isbn>", "/rebuy/<isbn>", "/all/<isbn>"]}
    }, 200


@app.route("/rebuy/<isbn>")
def getPrice_rebuy(isbn: str):  # type: ignore
    try:
        price = rebuy(context, isbn)
    except ValueError as e:
        return {
            "status_code": "422",
            "message": "Unprocessable Content",
            "context": str(e),
        }, 422
    except TimeoutError as e:
        return {
            "status_code": "504",
            "message": "Timeout while processing request",
            "context": str(e),
        }, 504
    else:
        return {"status_code": "200", "rebuy_price": str(price)}, 200


@app.route("/momox/<isbn>")
def getPrice_momox(isbn: str):  # type: ignore
    try:
        price = momox(context, isbn)
    except ValueError as e:
        return {
            "status_code": "422",
            "message": "Unprocessable Content",
            "context": str(e),
        }, 422
    except TimeoutError as e:
        return {
            "status_code": "504",
            "message": "Timeout while processing request",
            "context": str(e),
        }, 504
    else:
        return {"status_code": "200", "momox_price": str(price)}, 200


@app.route("/all/<isbn>")
def getPrice_all(isbn: str):  # type: ignore
    try:
        rebuy_price = rebuy(context, isbn)
        momox_price = momox(context, isbn)
    except ValueError as e:
        return {
            "status_code": "422",
            "message": "Unprocessable Content",
            "context": str(e),
        }, 422
    except TimeoutError as e:
        return {
            "status_code": "504",
            "message": "Timeout while processing request",
            "context": str(e),
        }, 504
    else:
        return {
            "status_code": "200",
            "rebuy_price": str(rebuy_price),
            "momox_price": str(momox_price),
        }, 200


if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", "5000"))
        app.run(host="0.0.0.0", port=port, debug=False)
    finally:
        stop_playwright(browser)
