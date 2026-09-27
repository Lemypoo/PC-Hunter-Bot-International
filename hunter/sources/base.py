"""Shared building blocks for retailer sources."""
import re
from dataclasses import dataclass, asdict
from typing import Optional

from .. import countries
from ..money import parse_money, parse_price   # noqa: F401  (sources import parse_price from here)


@dataclass
class Listing:
    source: str
    source_name: str
    id: str
    title: str
    url: str
    price: Optional[float]
    currency: str = "USD"
    in_stock: bool = True
    condition: str = ""
    location: str = ""
    seller: str = ""
    was_price: Optional[float] = None
    sponsored: bool = False
    category: str = ""      # store's own category label, checked by the exclude filter too
    region: str = ""        # the country setting it was found under; set by the checker if a store leaves it out

    @property
    def key(self) -> str:
        # the same Amazon ASIN in Germany and in Japan is two listings in two currencies
        return f"{self.source}:{self.region}:{self.id}" if self.region else f"{self.source}:{self.id}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["key"] = self.key
        return d


class SourceError(Exception):
    """A source could not be read (blocked, layout changed, network)."""


BLOCK_TITLES = (
    "access denied", "just a moment", "robot check", "something went wrong",
    "are you a human", "security verification", "error page", "attention required",
)
# Some blocks come as a near-empty page with no title at all; then the body text is the tell.
# Amazon's robot check keeps the normal "Amazon.xx" title and says "not a robot" instead.
BLOCK_BODY_RE = re.compile(r"access denied|access to this page has been denied|request blocked|forbidden|"
                           r"verify you are human|are you a robot|not a robot|captcha|unusual traffic|"
                           r"enter the characters you see below|type the characters you see|"
                           r"geben sie die zeichen unten ein|saisissez les caractères|"
                           r"inserisci i caratteri|introduce los caracteres", re.I)


class Source:
    key = ""
    name = ""
    regions = None     # countries this store serves; None means "ask supports()"
    retail = True      # a real shop, whose prices anchor the "too cheap to be real" floor
    min_gap = 10       # seconds between two requests to this store; raised for stores that block bursts
    interval = 300     # seconds before one item is checked at this store again

    def __init__(self, settings: dict):
        self.settings = settings

    @classmethod
    def supports(cls, region: str) -> bool:
        return region in (cls.regions or ())

    def display_name(self, region: str) -> str:
        return self.name

    def note(self, region: str) -> str:
        """Anything the user should know about this store in this country (shown in Settings)."""
        return ""

    @staticmethod
    def currency(region: str) -> str:
        return countries.currency(region)

    def search(self, page, query: str, region: str) -> list:
        raise NotImplementedError

    def _check_blocked(self, page):
        title = (page.title() or "").strip()
        if any(b in title.lower() for b in BLOCK_TITLES):
            raise SourceError(f"blocked (page title: '{title[:60]}')")
        try:
            body = page.evaluate("() => document.body ? document.body.innerText.slice(0, 2000) : ''")
        except Exception:
            return
        if len(body) < 600 and BLOCK_BODY_RE.search(body):
            raise SourceError(f"blocked ({' '.join(body.split())[:80]})")

    def goto(self, page, url: str, wait_for: str = None, timeout: int = 45000, settle: int = 1500):
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        self._check_blocked(page)
        if wait_for:
            try:
                page.wait_for_selector(wait_for, timeout=15000)
            except Exception:
                pass  # zero results is legitimate; the caller decides
        page.wait_for_timeout(settle)
        self._check_blocked(page)


def site_label(domain: str) -> str:
    """'amazon.co.uk' -> 'Amazon.co.uk', 'www.befr.ebay.be' -> 'eBay.be'."""
    d = domain.lower().removeprefix("www.")
    if "ebay." in d:
        return "eBay." + d.split("ebay.", 1)[1]
    return d[:1].upper() + d[1:]
