from flask import Flask
from typing import Optional

from app.config import configure_logging
from app.browser_utils import start_playwright
from app.routes import create_routes


def create_app(
    browser_type: str = "chromium",
    use_obfuscation: bool = True,
    app_name: str = "Booksell-backend",
) -> tuple[Flask, object, object]:
    """Application factory function

    Creates and configures a Flask application instance with browser context.

    Args:
        browser_type (str, optional): Type of browser to use. Defaults to "chromium".
        use_obfuscation (bool, optional): Whether to use obfuscation headers. Defaults to True.
        app_name (str, optional): Name of the Flask application. Defaults to "Booksell-backend".

    Returns:
        tuple[Flask, Browser, BrowserContext]: Configured Flask app, browser instance, and browser context
    """
    # Configure logging
    configure_logging()

    # Create Flask app
    app = Flask(app_name)

    # Initialize browser and context
    browser, context = start_playwright(
        browsertype=browser_type,
        use_obfuscation_headers=use_obfuscation,
    )

    # Register routes with browser context
    routes_bp = create_routes(context)
    app.register_blueprint(routes_bp)

    return app, browser, context
