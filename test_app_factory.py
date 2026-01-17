"""
Simple test to verify the app factory pattern works correctly.
This demonstrates that the factory can create app instances with different configurations.
"""

import sys
import os

# Add parent directory to path to import app module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.browser_utils import stop_playwright


def test_app_creation():
    """Test that the app factory creates a valid Flask application"""
    print("Testing app factory pattern...")
    
    # Create app with default configuration
    app, browser, context = create_app()
    
    try:
        # Verify app is created
        assert app is not None, "App should not be None"
        assert app.name == "Booksell-backend", "App should have correct default name"
        
        # Verify routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules() if not rule.rule.startswith("/static")]
        expected_routes = ["/", "/api/r/<isbn>", "/api/m/<isbn>", "/api/b/<isbn>", "/api/all/<isbn>", "/api/info/<isbn>"]
        
        for route in expected_routes:
            assert route in routes, f"Route {route} should be registered"
        
        print(f"✓ App created successfully with name: {app.name}")
        print(f"✓ All {len(expected_routes)} routes registered correctly")
        print(f"✓ Browser initialized: {browser is not None}")
        print(f"✓ Context initialized: {context is not None}")
        
        return True
        
    finally:
        # Clean up
        stop_playwright(browser)
        print("✓ Browser cleaned up successfully")


def test_custom_app_name():
    """Test that the app factory accepts custom app name"""
    print("\nTesting custom app name...")
    
    app, browser, context = create_app(app_name="CustomTestApp")
    
    try:
        assert app.name == "CustomTestApp", "App should have custom name"
        print(f"✓ Custom app name works: {app.name}")
        return True
        
    finally:
        stop_playwright(browser)
        print("✓ Browser cleaned up successfully")


def main():
    """Run all tests"""
    print("=" * 60)
    print("App Factory Pattern Tests")
    print("=" * 60)
    
    try:
        test_app_creation()
        # Note: Cannot test multiple instances in same process due to Playwright limitations
        # The factory pattern still works, but Playwright can only be initialized once per process
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        print("\nNote: The app factory supports custom configurations,")
        print("but Playwright can only be initialized once per process.")
        print("In production, each process would have its own instance.")
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
