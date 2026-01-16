import logging
import requests
import os

from flask import Flask
from logging.config import dictConfig
from playwright.sync_api import sync_playwright, TimeoutError, Browser, BrowserContext
from typing import Literal

# Module imports
from bmx import buchmaxe
from mox import momox
from rby import rebuy


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
def home():
    return {"message": "GUI coming soon!"}, 200


@app.route("/api/r/<isbn>")
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


@app.route("/api/m/<isbn>")
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


@app.route("/api/b/<isbn>")
def getPrice_buchmaxe(isbn: str):
    try:
        price = buchmaxe(context, isbn)
    except ValueError as e:
        return {
            "status_code": 422,
            "message": "Unprocessable Content",
            "context": str(e),
        }, 422
    except TimeoutError as e:
        return {
            "status_code": 504,
            "message": "Timeout while processing request",
            "context": str(e),
        }, 504
    else:
        return {"status_code": 200, "buchmaxe_price": str(price)}, 200


@app.route("/api/all/<isbn>")
def getPrice_all(isbn: str):  # type: ignore
    try:
        rebuy_price = rebuy(context, isbn)
        momox_price = momox(context, isbn)
        buchmaxe_price = buchmaxe(context, isbn)
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
            "buchmaxe_price": str(buchmaxe_price),
        }, 200


@app.route("/api/info/<isbn>")
def get_book_info(isbn: str):
    try:
        isbn = isbn.replace("-", "")
        if not isbn.isdigit() or len(isbn) not in [10, 12, 13, 15, 16]:
            raise ValueError("Invalid isbn: {}".format(isbn))
        try:
            response = requests.get(
                f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}",
                timeout=10,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            return {
                "status_code": 504,
                "message": "Gateway Timeout: Google Books API did not respond in time",
            }, 504
        except requests.exceptions.HTTPError:
            return {
                "status_code": 503,
                "message": "The request to Google's Books API did not complete successfully",
            }, 503
        except Exception as e:
            return {
                "status_code": 500,
                "message": "An internal server error occurred during the processing of the request",
                "context": str(e),
            }, 500
        else:
            book_data = response.json()
            if book_data["totalItems"] == 0:
                return {"status_code": 422, "message": "Invalid ISBN"}, 422
            try:
                book = book_data["items"][0]["volumeInfo"]
                title = book["title"]
                authors = book["authors"]
                publish_year = book["publishedDate"].split("-")[0]
            except Exception as e:
                return {
                    "status_code": 500,
                    "message": "An error occurred during the parsing of Google's API response",
                    "context": str(e),
                }, 500
            else:
                return {
                    "title": title if title else "N/A",
                    "authors": authors if authors else "N/A",
                    "published_year": publish_year if publish_year else "N/A",
                    "status_code": 200,
                }, 200
    except Exception as e:
        return {
            "status_code": 500,
            "message": "An unknown error occurred during the processing of the request",
            "context": str(e),
        }, 500


if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", "5000"))
        app.run(host="0.0.0.0", port=port, debug=False)
    finally:
        stop_playwright(browser)
