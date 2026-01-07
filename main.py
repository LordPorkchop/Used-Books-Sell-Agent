from playwright.sync_api import sync_playwright, TimeoutError
import logging
from flask import Flask
import os


def rebuy(
    isbn: str,
    use_obfuscation_headers: bool = True,
    remote_debugging: bool = False,
    remote_debugging_port: int | None = None,
) -> float:

    if not isbn.isdigit() or len(isbn) not in [10, 12, 13, 15, 16]:
        raise ValueError("Invalid ISBN")

    with sync_playwright() as p:
        if remote_debugging:
            if remote_debugging_port is None:
                raise ValueError(
                    "remote_debugging_port must be provided when remote_debugging is True"
                )
            browser = p.chromium.launch(
                headless=False,
                args=[f"--remote-debugging-port={remote_debugging_port}"],
            )
        else:
            browser = p.chromium.launch(headless=True)

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

        page = context.new_page()

        logging.info("Initialized Playwright")

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
            browser.close()
            logging.info("Closed browser")
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
            browser.close()
            logging.info("Closed browser")
            return -1

        try:
            price_offer_element = page.locator('div[data-cy="product-price"]').first
            price_offer_element.wait_for(state="visible", timeout=2000)
            price_offer_text = price_offer_element.inner_text()
            price_offer = float(
                price_offer_text.replace("€", "").replace(",", ".").strip()
            )
            logging.info(f"Offer price: {price_offer} EUR")
            return price_offer
        except TimeoutError:
            logging.info("No offer available for this book")
            browser.close()
            logging.info("Closed browser")

        return -1  # Placeholder return value


def momox(
    isbn: str,
    use_obfuscation_headers: bool = True,
    remote_debugging: bool = False,
    remote_debugging_port: int | None = None,
) -> float:

    if not isbn.isdigit() or len(isbn) not in [10, 12, 13, 15, 16]:
        raise ValueError("Invalid ISBN")

    with sync_playwright() as p:
        if remote_debugging:
            if remote_debugging_port is None:
                raise ValueError(
                    "remote_debugging_port must be provided when remote_debugging is True"
                )
            browser = p.chromium.launch(
                headless=False,
                args=[f"--remote-debugging-port={remote_debugging_port}"],
            )
        else:
            browser = p.chromium.launch(headless=True)

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

        page = context.new_page()

        logging.info("Initialized Playwright")

        try:
            page.goto(
                "https://www.momox.de/buecher-verkaufen",
                referer="/",
                wait_until="domcontentloaded",
                timeout=5000,
            )
            logging.info("Opened Momox merchant page")
        except TimeoutError:
            browser.close()
            logging.info("Closed browser")

        try:
            isbn_input = page.locator(
                'input[class*="product-input"], input[class*="searchbox-input"]'
            ).first
            isbn_input.wait_for(state="visible", timeout=2000)
        except TimeoutError:
            logging.error("Failed to locate ISBN input")
            browser.close()
            logging.info("Closed browser")
            return -1
        else:
            logging.info("Found ISBN input")

        try:
            isbn_input.fill(isbn)
            logging.info(f"Filled ISBN: {isbn}")
            isbn_input.press("Enter")
        except TimeoutError:
            logging.error("Failed to fill or submit ISBN input")
            browser.close()
            logging.info("Closed browser")
            return -1

        page.wait_for_load_state("domcontentloaded")
        logging.info("Search results loaded")

        try:
            price_offer_element = page.locator(".searchresult-price").first
            price_offer_element.wait_for(state="visible", timeout=1000)
            price_offer_text = price_offer_element.inner_text()
            price_offer = float(
                price_offer_text.replace("€", "").replace(",", ".").strip()
            )
            logging.info(f"Offer price: {price_offer} EUR")
            browser.close()
            logging.info("Closed browser")
            logging.info(f'momox(isbn="{isbn}") -> {price_offer}')
            return price_offer
        except TimeoutError:
            logging.info("No offer available for this book")
            browser.close()
            logging.info("Closed browser")
            logging.info(f'momox(isbn="{isbn}") -> {-1}')

        return -1


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s.%(msecs)03d] [%(levelname)-8s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Add color to log levels
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        formatter: logging.Formatter = handler.formatter or logging.Formatter()

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
                record.levelname = (
                    f"{log_color}{record.levelname}{self.COLORS['RESET']}"
                )
                return super().format(record)

        handler.setFormatter(ColoredFormatter(formatter._fmt, formatter.datefmt))

app = Flask("BookResellerIntegration")


@app.route("/")
def showHelp():
    return {
        "help": {"commands": ["/momox/<isbn>", "/rebuy/<isbn>", "/all/<isbn>"]}
    }, 200


@app.route("/rebuy/<isbn>")
def getPrice_rebuy(isbn: str):  # type: ignore
    try:
        price = rebuy(isbn)
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


@app.route("/momox/<isbn>")
def getPrice_momox(isbn: str):  # type: ignore
    try:
        price = momox(isbn)
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
        rebuy_price = rebuy(isbn)
        momox_price = momox(isbn)
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
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
