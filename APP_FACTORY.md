# App Factory Pattern

This application has been refactored to use the **app factory design pattern**, which provides several benefits:

## Structure

```
app/
├── __init__.py          # Contains the create_app() factory function
├── config.py            # Logging configuration
├── browser_utils.py     # Playwright browser utilities
├── routes.py            # Application routes (Blueprint)
├── bmx.py              # Buchmaxe scraper module
├── mox.py              # Momox scraper module
└── rby.py              # Rebuy scraper module

main.py                  # Application entry point
```

## Usage

### Basic Usage

```python
from app import create_app
from app.browser_utils import stop_playwright

# Create app with default configuration
app, browser, context = create_app()

# Run the app
if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
    finally:
        stop_playwright(browser)
```

### Custom Configuration

The `create_app()` factory function accepts optional parameters for configuration:

```python
app, browser, context = create_app(
    browser_type="chromium",      # Browser type: "chromium", "firefox", or "webkit"
    use_obfuscation=True,         # Use obfuscation headers to avoid bot detection
    app_name="Booksell-backend"   # Flask application name
)
```

## Benefits

1. **Modularity**: Configuration and initialization logic are separated from route definitions
2. **Testability**: Easy to create app instances with different configurations for testing
3. **Flexibility**: Can create multiple app instances with different settings
4. **Clean Separation**: Browser utilities, configuration, and routes are in separate modules
5. **Blueprint Pattern**: Routes are organized using Flask Blueprints for better organization

## Components

### `create_app()` Factory Function

The factory function in `app/__init__.py`:
- Configures logging
- Creates Flask app instance
- Initializes Playwright browser and context
- Registers route blueprints
- Returns app, browser, and context for external management

### Configuration (`app/config.py`)

Contains logging configuration with colored output formatting.

### Browser Utilities (`app/browser_utils.py`)

Provides:
- `start_playwright()`: Initializes browser with optional obfuscation
- `stop_playwright()`: Properly closes browser instances

### Routes (`app/routes.py`)

Defines all API endpoints using Flask Blueprints:
- `/` - Home endpoint
- `/api/r/<isbn>` - Rebuy price lookup
- `/api/m/<isbn>` - Momox price lookup
- `/api/b/<isbn>` - Buchmaxe price lookup
- `/api/all/<isbn>` - All prices lookup
- `/api/info/<isbn>` - Book information from Google Books API
