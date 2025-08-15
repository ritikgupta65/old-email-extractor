from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import re
from urllib.parse import urljoin

app = Flask(__name__)

COMMON_LINK_TEXTS = ['About Us', 'Contact Us','contact', 'about','support', 'help']

def extract_emails_from_page(page):
    content = page.content()
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", content)
    return list(set(emails))

def click_visible_links(page):
    for text in COMMON_LINK_TEXTS:
        links = page.locator(f"a:has-text('{text}')")
        if links.count() > 0:
            try:
                links.first.click()
                page.wait_for_timeout(3000)
                return True
            except:
                continue
    return False

def extract_emails(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(4000)

            # Click common menu buttons like hamburger
            menu_button = page.locator("button[aria-label*='menu' i]")
            if menu_button.count() > 0:
                try:
                    menu_button.first.click()
                    page.wait_for_timeout(2000)
                except:
                    pass

            # Try clicking common links (Contact, About, etc.)
            clicked = click_visible_links(page)

            # Grab emails from this or redirected page
            emails = extract_emails_from_page(page)
            return {"emails": emails}

        except Exception as e:
            return {"error": str(e)}
        finally:
            browser.close()

@app.route('/extract-email', methods=['POST'])
def extract_email_api():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' in request."}), 400

    result = extract_emails(url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5002)  
    
    