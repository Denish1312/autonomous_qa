from playwright.sync_api import sync_playwright

def test_basic_navigation():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch()
        
        # Create a new page
        page = browser.new_page()
        
        try:
            # Navigate to a test website
            page.goto('https://example.com')
            
            # Get the title
            title = page.title()
            print(f"✅ Successfully loaded page. Title: {title}")
            
            # Take a screenshot
            page.screenshot(path="tests/test_screenshot.png")
            print("✅ Successfully captured screenshot")
            
            # Test passed
            print("✅ Playwright test passed!")
            return True
            
        except Exception as e:
            print(f"❌ Error during Playwright test: {str(e)}")
            return False
            
        finally:
            # Clean up
            browser.close()

if __name__ == "__main__":
    test_basic_navigation()
