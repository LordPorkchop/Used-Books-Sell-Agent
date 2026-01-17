import logging
from playwright.sync_api import BrowserContext, TimeoutError


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
