import logging
from playwright.sync_api import BrowserContext, TimeoutError


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
