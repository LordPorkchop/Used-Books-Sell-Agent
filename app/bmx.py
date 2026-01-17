import logging
from playwright.sync_api import BrowserContext


def buchmaxe(context: BrowserContext, isbn: str) -> float:
    if not isbn.isdigit() or len(isbn) not in [10, 12, 13, 15, 16]:
        raise ValueError("Invalid ISBN")

    page = context.new_page()

    try:
        page.goto("https://www.buchmaxe.de")
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except TimeoutError:
        logging.error("buchmaxe.de timed out after 5000ms")
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
