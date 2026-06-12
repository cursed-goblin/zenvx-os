"""web_browser.py - Playwright (Chromium headless) browser automation."""


class WebBrowser:
    def __init__(self, nav_timeout=10000, action_timeout=5000):
        self.nav_timeout = nav_timeout
        self.action_timeout = action_timeout
        self._pw = None
        self._browser = None
        self._page = None

    def _ensure(self):
        if self._page is not None:
            return
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._page = self._browser.new_page()

    def navigate(self, url):
        if not (url.startswith("http://") or url.startswith("https://")):
            return "Only http/https URLs are permitted."
        self._ensure()
        self._page.goto(url, timeout=self.nav_timeout)
        return self._page.title()

    def get_text(self, selector):
        self._ensure()
        el = self._page.query_selector(selector)
        return el.inner_text() if el else ""

    def click(self, selector):
        self._ensure()
        self._page.click(selector, timeout=self.action_timeout)

    def type_text(self, selector, text):
        self._ensure()
        self._page.fill(selector, text, timeout=self.action_timeout)

    def screenshot(self, path="/tmp/zenvx_browser.png"):
        self._ensure()
        self._page.screenshot(path=path)
        return path

    def close(self):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
        self._page = self._browser = self._pw = None
