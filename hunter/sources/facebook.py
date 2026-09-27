import re
from urllib.parse import quote_plus, unquote

from .. import countries
from ..money import is_price_only
from ..store import part_category
from .base import Listing, Source, SourceError, parse_money

# Badges Facebook prints on a card; none of them is the listing's title.
BADGES = {"just listed", "pending", "sold", "free", "shipping available", "new", "price dropped"}

# Facebook's search answers "No listings found" for some bare model numbers ("9950X3D", checked in
# September 2026) while "cpu 9950X3D" finds the very listings it should have. An empty answer is
# retried once with the part's category in front, and the wording that works is remembered.
_wording = {}          # (city, query) -> the search text Facebook answers

JS = r"""() => [...document.querySelectorAll('a[href*="/marketplace/item/"]')].map(a => {
  const spans = [...a.querySelectorAll('span')].map(s => (s.innerText || '').trim()).filter(Boolean);
  return { href: a.getAttribute('href') || '', spans: [...new Set(spans)] };
})"""
CITY_IN_URL = re.compile(r"/marketplace/([^/?#]+)")


def city_slug(raw: str) -> str:
    """What goes in the address: 'London' -> 'london', 'Kuala Lumpur' -> 'kualalumpur', ids unchanged."""
    return re.sub(r"[\s/]+", "", (raw or "").strip().lower())


class Facebook(Source):
    key = "facebook"
    name = "Facebook Marketplace"
    retail = False
    min_gap = 20
    interval = 300

    @classmethod
    def supports(cls, region):
        return countries.selectable(region) and region not in countries.NO_MARKETPLACE

    def note(self, region):
        if not city_slug(self.settings.get("fb_city")):
            return "needs your city below"
        return ""

    def search(self, page, query, region):
        city = city_slug(self.settings.get("fb_city"))
        if not city:
            raise SourceError("no Facebook city set; type yours in Settings")
        key = (city, query.strip().lower())
        words = _wording.get(key, query)
        rows = self._rows(page, city, words)
        cat = part_category(query)
        if not rows and words == query and cat and cat not in query.lower().split():
            page.wait_for_timeout(2000)
            broader = f"{cat} {query}"
            rows = self._rows(page, city, broader)
            if rows:
                _wording[key] = broader
        return self._parse(rows, region)

    def _rows(self, page, city, words):
        """The raw result cards for one search, or [] when Facebook says there are none."""
        url = f"https://www.facebook.com/marketplace/{quote_plus(city)}/search/?query={quote_plus(words)}"
        page.goto(url, timeout=45000, wait_until="domcontentloaded")
        landed = CITY_IN_URL.search(unquote(page.url or ""))
        if "/login" in (page.url or ""):
            raise SourceError("blocked (Facebook wants a login before showing Marketplace)")
        got = landed.group(1).lower() if landed else city
        # an unknown name lands on /marketplace/category/; a numeric city id may come back as its name
        if got == "category" or (got != city and not city.isdigit()):
            # Facebook swaps a city it does not know for one near your internet connection, silently
            raise SourceError(f"Facebook does not recognise the city '{city}'. In Settings, use the word "
                              f"after /marketplace/ in Facebook's own address for your city")
        try:   # either listings or the "nothing here" message; whichever comes first
            page.wait_for_selector('a[href*="/marketplace/item/"], :text("No listings found")', timeout=12000)
        except Exception:
            pass
        rows = page.evaluate(JS)
        if not rows:
            page.wait_for_timeout(1500)
            rows = page.evaluate(JS)
        if not rows:
            body = page.evaluate("() => document.body ? document.body.innerText : ''")
            if "No listings found" in body or "Try a new search" in body:
                return []
            # no listings and no "nothing found" message: Facebook is holding the page back (login wall);
            # the word "blocked" makes the scheduler leave it alone for a while instead of hammering it
            raise SourceError("blocked (Facebook is not showing Marketplace results to this browser right now)")
        return rows

    def _parse(self, rows, region):
        home = self.currency(region)
        out, seen = [], set()
        for r in rows:
            m = re.search(r"/marketplace/item/(\d+)", r.get("href") or "")
            if not m or m.group(1) in seen:
                continue
            fb_id = m.group(1)
            spans = r.get("spans") or []
            prices = [s for s in spans if is_price_only(s, home)]
            others = [s for s in spans if s not in prices and "\n" not in s
                      and s.strip().lower() not in BADGES]
            if not prices or not others:
                continue  # "Free" listings or unparseable cards
            price, cur = parse_money(prices[0], home)
            was, was_cur = parse_money(prices[1], home) if len(prices) > 1 else (None, None)
            if price is None:
                continue
            title = others[0]
            location = ""
            if len(others) > 1:
                cand = others[-1]
                if cand != title and len(cand) <= 60 and ("," in cand or "km" in cand.lower()):
                    location = cand
            flags = {s.strip().lower() for s in spans}
            seen.add(fb_id)
            out.append(Listing(
                source=self.key, source_name=self.name, id=fb_id, title=title,
                url=f"https://www.facebook.com/marketplace/item/{fb_id}/", price=price,
                currency=cur or home, in_stock=not ({"pending", "sold"} & flags),
                condition="Used / local", location=location,
                was_price=was if (was and was > price and was_cur == cur) else None, region=region,
            ))
        return out
