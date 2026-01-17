import os

from app import create_app
from app.browser_utils import stop_playwright


# Create app instance using factory
app, browser, context = create_app()


if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", "5000"))
        app.run(host="0.0.0.0", port=port, debug=False)
    finally:
        stop_playwright(browser)
