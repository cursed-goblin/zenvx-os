"""web_search.py - DuckDuckGo search with rate limiting and caching."""
import time
import urllib.parse
import urllib.request

try:
    from duckduckgo_search import DDGS
    _HAS_DDGS = True
except Exception:  # noqa: BLE001
    _HAS_DDGS = False


class WebSearch:
    def __init__(self, cache_ttl=86400):
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._last_request = 0.0

    def _rate_limit(self):
        delta = time.time() - self._last_request
        if delta < 1.0:
            time.sleep(1.0 - delta)
        self._last_request = time.time()

    def search(self, query, max_results=5):
        now = time.time()
        if query in self._cache:
            value, ts = self._cache[query]
            if now - ts < self.cache_ttl:
                return value
        self._rate_limit()
        if _HAS_DDGS:
            try:
                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append((r.get("title", ""), r.get("href", ""),
                                        r.get("body", "")))
                formatted = self._format(results)
                self._cache[query] = (formatted, now)
                return formatted
            except Exception:  # noqa: BLE001
                pass
        return self._fallback(query)

    def _fallback(self, query):
        url = "https://html.duckduckgo.com/html/?q=" + \
            urllib.parse.quote(query)
        try:
            req = urllib.request.Request(url, headers={"User-Agent":
                                                       "zenvx/0.1"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", "ignore")
            return f"Raw results for '{query}' ({len(body)} bytes)."
        except Exception as exc:  # noqa: BLE001
            return f"Search failed: {exc}"

    @staticmethod
    def _format(results):
        lines = []
        for title, url, snippet in results:
            lines.append(f"- {title}\n  {url}\n  {snippet[:200]}")
        return "\n".join(lines) if lines else "No results."
