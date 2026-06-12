"""ecommerce_handler.py - Amazon, Flipkart, Meesho product automation."""

VENDOR_CONFIGS = {
    "amazon": {
        "search_url": "https://www.amazon.in/s?k={query}",
        "container": "div[data-component-type='s-search-result']",
        "title": "h2 span",
        "price": "span.a-price-whole",
        "link": "h2 a",
    },
    "flipkart": {
        "search_url": "https://www.flipkart.com/search?q={query}",
        "container": "div._1AtVbE",
        "title": "div._4rR01T",
        "price": "div._30jeq3",
        "link": "a._1fQZEK",
    },
    "meesho": {
        "search_url": "https://www.meesho.com/search?q={query}",
        "container": "div[class*='ProductList__GridCol']",
        "title": "p[class*='Text']",
        "price": "h5",
        "link": "a",
    },
}


class Product:
    def __init__(self, title, price, url, vendor, rating=None):
        self.title = title
        self.price = price
        self.url = url
        self.vendor = vendor
        self.rating = rating

    def __repr__(self):
        return f"<Product {self.title!r} {self.price} {self.vendor}>"


class EcommerceHandler:
    def __init__(self, browser):
        self.browser = browser

    @staticmethod
    def _parse_price(text):
        digits = "".join(c for c in str(text) if c.isdigit() or c == ".")
        try:
            return float(digits)
        except ValueError:
            return float("inf")

    def search_products(self, vendor, query, limit=10):
        cfg = VENDOR_CONFIGS.get(vendor)
        if not cfg:
            return []
        url = cfg["search_url"].format(query=query.replace(" ", "+"))
        self.browser.navigate(url)
        products = []
        try:
            self.browser._ensure()
            cards = self.browser._page.query_selector_all(cfg["container"])
        except Exception:  # noqa: BLE001
            cards = []
        for card in cards[:limit]:
            try:
                title_el = card.query_selector(cfg["title"])
                price_el = card.query_selector(cfg["price"])
                link_el = card.query_selector(cfg["link"])
                title = title_el.inner_text() if title_el else ""
                price = self._parse_price(price_el.inner_text()
                                          if price_el else "")
                href = link_el.get_attribute("href") if link_el else ""
                products.append(Product(title, price, href, vendor))
            except Exception:  # noqa: BLE001
                continue
        return products

    @staticmethod
    def filter_by_price(products, max_price):
        return [p for p in products if p.price <= max_price]

    @staticmethod
    def rank_by_value(products):
        ranked = sorted(
            products,
            key=lambda p: (p.price, -(p.rating or 0)))
        lines = [f"{i}. {p.title[:60]} - \u20b9{p.price} ({p.vendor})"
                 for i, p in enumerate(ranked, 1)]
        return "\n".join(lines) if lines else "No products found."
