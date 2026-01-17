import requests
from flask import Blueprint
from playwright.sync_api import TimeoutError

from app.bmx import buchmaxe
from app.mox import momox
from app.rby import rebuy


def create_routes(context):
    """Create and configure routes blueprint with browser context

    Args:
        context: Playwright browser context to use for scraping

    Returns:
        Blueprint: Configured routes blueprint
    """
    bp = Blueprint("routes", __name__)

    @bp.route("/")
    def home():
        return {"message": "GUI coming soon!"}, 200

    @bp.route("/api/r/<isbn>")
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

    @bp.route("/api/m/<isbn>")
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

    @bp.route("/api/b/<isbn>")
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

    @bp.route("/api/all/<isbn>")
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

    @bp.route("/api/info/<isbn>")
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

    return bp
