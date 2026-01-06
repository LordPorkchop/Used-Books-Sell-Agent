from playwright.sync_api import sync_playwright, TimeoutError
import logging
from flask import Flask, jsonify
import os

# Configure logging at MODULE LEVEL
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s.%(msecs)03d] [%(levelname)-8s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# CREATE FLASK APP AT MODULE LEVEL
app = Flask("BookResellerIntegration")

# UNFINISHED
def thalia(isbn: str,
           use_obfuscation_headers: bool = True,
           remote_debugging: bool = False,
           remote_debugging_port: int | None = None
           ) -> float:
    
    if not isbn.isdigit() or len(isbn) not in [10, 12, 13, 15, 16]:
        raise ValueError("Invalid ISBN")

    with sync_playwright() as p:
        if remote_debugging:
            if remote_debugging_port is None:
                raise ValueError("remote_debugging_port must be provided when remote_debugging is True")
            browser = p.chromium.launch(
                headless=False,
                args=[f"--remote-debugging-port={remote_debugging_port}"]
            )
        else:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )

        if use_obfuscation_headers:
            context = browser.new_context(
                locale="de-DE",
                timezone_id="Europe/Berlin",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "de-DE,de;q=0.9",
                }
            )
        else:
            context = browser.new_context()
        
        page = context.new_page()

        logging.info("Initialized Playwright")

        try:
            page.goto("https://www.thalia.de/versandbox/artikel/eingeben", referer="/gebrauchtbuch/verkauf", wait_until="domcontentloaded", timeout=5000)
            logging.info("Opened Thalia merchant page")
        except TimeoutError:
            logging.error('"https://www.thalia.de/versandbox/artikel/eingeben" timed out after 5s')
            browser.close()
            logging.info("Closed browser")
            return -1
        
        try:
            close_btn = page.locator('html body layout-fullsize main#content.layout-main div.layout-content div.component-content versandbox-qualitaetspruefungsoverlay dialog.element-overlay-small div.actions button.element-button-primary.submit-button')
            close_btn.wait_for(state="visible", timeout=2000)
            logging.info("Quality check popup detected")
            close_btn.click()
            close_btn.wait_for(state="hidden", timeout=2000)
            logging.info("Closed quality check popup")

        except TimeoutError:
            logging.info("No quality check popup detected")
        

        try:
            cookie_btn = page.locator('button:has-text("Alle akzeptieren")')
            cookie_btn.wait_for(state="visible", timeout=2000)
            logging.info("Cookie consent popup detected")
            cookie_btn.click()
            cookie_btn.wait_for(state="hidden", timeout=2000)
            logging.info("Accepted cookies")
        except TimeoutError:
            logging.info("No cookie consent popup detected")
        

        
        text_input_btn = page.locator('button[id="versandbox-eingabe-text-input"]')
        text_input_btn.click()
        logging.info("Switched to text input mode")

        isbn_input = page.locator('input[name="eingabe"]')
        logging.info("Found ISBN input")
        isbn_input.fill(isbn)
        logging.info(f"Filled ISBN: {isbn}")

        submit_btn = page.locator('button[id="versandbox-eingabe-text-input"]')
        submit_btn.click()
        logging.info("Submitted ISBN")

        page.wait_for_load_state("domcontentloaded")
        logging.info("Offer page loaded")

        offer_dialog = page.locator("html body.dialog-open layout-fullsize main#content.layout-main div.layout-content div.component-content versandbox-bestaetigen-overlay dialog.element-overlay-small.dialog-angebot")
        no_offer_dialog = page.locator('html body.dialog-open layout-fullsize main#content.layout-main div.layout-content div.component-content versandbox-bestaetigen-overlay dialog.element-overlay-small.dialog-nicht-gefunden')
        not_found_dialog = page.locator('html body.dialog-open layout-fullsize main#content.layout-main div.layout-content div.component-content versandbox-bestaetigen-overlay dialog.element-overlay-small.dialog-kein-ankauf')

        
        if offer_dialog.is_hidden():
            if no_offer_dialog.is_hidden():
                if not_found_dialog.is_hidden():
                    logging.error("None of the expected dialogs appeared")
                    browser.close()
                    logging.info("Closed browser")
                    return -1
                else:
                    logging.info("Book not found")
                    browser.close()
                    logging.info("Closed browser")
                    return -1
            else:
                logging.info("No offer available for this book")
                browser.close()
                logging.info("Closed browser")
                return -1

        try:
            offer_price_element = page.locator('p[class*="artikel-preis"]')
            offer_price_element.wait_for(state="visible", timeout=500)
            offer_price_text = offer_price_element.inner_text()
            offer_price = float(offer_price_text.replace("€", "").replace(",", ".").strip())
            logging.info(f"Offer price: {offer_price} EUR")
        except TimeoutError:
            logging.error("Failed to locate offer price element")
            browser.close()
            logging.info("Closed browser")
            logging.info(f'thalia(isbn="{isbn}") -> {-1}')
            return -1
        else:
            browser.close()
            logging.info("Closed browser")
            logging.info(f'thalia(isbn="{isbn}") -> {offer_price}')
            return offer_price
            

def rebuy(isbn: str,
           use_obfuscation_headers: bool = True,
           remote_debugging: bool = False,
           remote_debugging_port: int | None = None
           ) -> float:
    
    if not isbn.isdigit() or len(isbn) not in [10, 12, 13, 15, 16]:
        raise ValueError("Invalid ISBN")

    with sync_playwright() as p:
        if remote_debugging:
            if remote_debugging_port is None:
                raise ValueError("remote_debugging_port must be provided when remote_debugging is True")
            browser = p.chromium.launch(
                headless=False,
                args=[f"--remote-debugging-port={remote_debugging_port}"]
            )
        else:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )

        if use_obfuscation_headers:
            context = browser.new_context(
                locale="de-DE",
                timezone_id="Europe/Berlin",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "de-DE,de;q=0.9",
                }
            )
        else:
            context = browser.new_context()
        
        page = context.new_page()

        logging.info("Initialized Playwright")

        try:
            page.goto("https://www.rebuy.de/verkaufen/buecher", referer="/verkaufen", wait_until="domcontentloaded", timeout=5000)
            logging.info("Opened Rebuy merchant page")
        except TimeoutError:
            logging.error('"https://www.rebuy.de/verkaufen/buecher" timed out after 5s')
            browser.close()
            logging.info("Closed browser")
            return -1
        
        try:
            isbn_input = page.locator('input[id="s_input5"], input[class*="search-input"]').first
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
            price_offer = float(price_offer_text.replace("€", "").replace(",", ".").strip())
            logging.info(f"Offer price: {price_offer} EUR")
            return price_offer
        except TimeoutError:
            logging.info("No offer available for this book")
            browser.close()
            logging.info("Closed browser")
        

        return -1  # Placeholder return value


def momox(isbn: str,
           use_obfuscation_headers: bool = True,
           remote_debugging: bool = False,
           remote_debugging_port: int | None = None
           ) -> float:
    
    if not isbn.isdigit() or len(isbn) not in [10, 12, 13, 15, 16]:
        raise ValueError("Invalid ISBN")

    with sync_playwright() as p:
        if remote_debugging:
            if remote_debugging_port is None:
                raise ValueError("remote_debugging_port must be provided when remote_debugging is True")
            browser = p.chromium.launch(
                headless=False,
                args=[f"--remote-debugging-port={remote_debugging_port}"]
            )
        else:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )

        if use_obfuscation_headers:
            context = browser.new_context(
                locale="de-DE",
                timezone_id="Europe/Berlin",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "de-DE,de;q=0.9",
                }
            )
        else:
            context = browser.new_context()
        
        page = context.new_page()

        logging.info("Initialized Playwright")

        try:
            page.goto("https://www.momox.de/buecher-verkaufen", referer="/", wait_until="domcontentloaded", timeout=5000)
            logging.info("Opened Momox merchant page")
        except TimeoutError:
            browser.close()
            logging.info("Closed browser")
        
        try:
            isbn_input = page.locator('input[class*="product-input"], input[class*="searchbox-input"]').first
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
            price_offer_element = page.locator('.searchresult-price').first
            price_offer_element.wait_for(state="visible", timeout=1000)
            price_offer_text = price_offer_element.inner_text()
            price_offer = float(price_offer_text.replace("€", "").replace(",", ".").strip())
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


# DEFINE ROUTES AT MODULE LEVEL
@app.route("/thalia/<isbn>")
def getPrice_thalia(isbn: str):
    return {"status_code": "501", "message": "Not Implemented"}, 501

@app.route("/rebuy/<isbn>")
def getPrice_rebuy(isbn: str):
    try:
        price = rebuy(isbn)
    except ValueError as e:
        return {"status_code": "422", "message": "Unprocessable Content", "context": str(e)}, 422
    except TimeoutError as e:
        return {"status_code": "504", "message": "Timeout while processing request", "context": str(e)}, 504
    else:
        return {"status_code": "200", "rebuy_price": str(price)}, 200

@app.route("/momox/<isbn>")
def getPrice_momox(isbn: str):
    try:
        price = momox(isbn)
    except ValueError as e:
        return {"status_code": "422", "message": "Unprocessable Content", "context": str(e)}, 422
    except TimeoutError as e:
        return {"status_code": "504", "message": "Timeout while processing request", "context": str(e)}, 504
    else:
        return {"status_code": "200", "momox_price": str(price)}, 200

@app.route("/all/<isbn>")
def getPrice_all(isbn: str):
    try:
        rebuy_price = rebuy(isbn)
        momox_price = momox(isbn)
    except ValueError as e:
        return {"status_code": "422", "message": "Unprocessable Content", "context": str(e)}, 422
    except TimeoutError as e:
        return {"status_code": "504", "message": "Timeout while processing request", "context": str(e)}, 504
    else:
        return {
            "status_code": "200",
            "rebuy_price": str(rebuy_price),
            "momox_price": str(momox_price)
        }, 200

# For local development only
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)

    