"""Prices in every format stores print them, and conversion between currencies.

Reading: "£1,299.00", "1.299,00 €", "EUR 172,57", "CHF1,100", "¥112,900", "₹1,23,456.00" and so on,
each into (amount, currency). The currency printed on the price wins over the store's usual one,
because eBay and Facebook show listings in whatever currency the seller used.

Converting: only needed when a listing's currency differs from the country's (Amazon.de seen from
Switzerland, a Bulgarian Facebook listing still in leva). Rates come from open.er-api.com once or twice
a day, with a second free source as backup, and are kept in data/rates.json between runs.
"""
import json
import os
import re
import threading
import time
import urllib.request
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATES_FILE = os.path.join(BASE_DIR, "data", "rates.json")
RATES_MAX_AGE = 12 * 3600
RATES_RETRY = 10 * 60          # after a failed download, wait this long before asking again
RATE_SOURCES = (
    ("https://open.er-api.com/v6/latest/USD", lambda d: d.get("rates") if d.get("result") == "success" else None),
    ("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json",
     lambda d: {k.upper(): v for k, v in (d.get("usd") or {}).items() if isinstance(v, (int, float))}),
)
RATES_CREDIT = "Exchange rates by open.er-api.com (ExchangeRate-API)"

# Currencies whose prices are written with no cents, and the few that use three decimals.
ZERO_DECIMALS = {"JPY", "KRW", "VND", "CLP", "ISK", "PYG", "UGX", "XOF", "XAF", "XPF", "KMF", "GNF",
                 "RWF", "BIF", "DJF", "VUV", "IDR", "HUF", "COP", "TWD", "IQD", "LAK", "MMK", "UZS"}
THREE_DECIMALS = {"KWD", "BHD", "OMR", "JOD", "TND", "LYD"}

# Markers written next to a price, longest first so "US $" wins over "$" and "R$" over "R".
# A currency given as a set is ambiguous: it means the store's own currency when that is in the set
# ("$" on Amazon.com.mx is pesos, "kr" on a Danish listing is kroner), otherwise the first choice.
_DOLLARS = ("USD", "CAD", "AUD", "NZD", "HKD", "SGD", "MXN", "ARS", "CLP", "COP", "UYU", "TWD", "BSD",
            "BBD", "BZD", "BMD", "KYD", "JMD", "TTD", "XCD", "FJD", "SBD", "LRD", "GYD", "SRD",
            "BND", "DOP", "CUP", "WST", "TOP", "NAD")
_MARKERS = [
    ("US $", "USD"), ("US$", "USD"), ("C $", "CAD"), ("CA$", "CAD"), ("C$", "CAD"), ("AU $", "AUD"),
    ("AU$", "AUD"), ("A$", "AUD"), ("NZ$", "NZD"), ("HK$", "HKD"), ("S$", "SGD"), ("MX$", "MXN"),
    ("R$", "BRL"), ("NT$", "TWD"), ("N$", "NAD"), ("RM", "MYR"), ("Rp", "IDR"),
    ("Rs.", ("INR", "PKR", "LKR", "NPR")), ("Rs", ("INR", "PKR", "LKR", "NPR")), ("S/", "PEN"),
    ("zł", "PLN"), ("Kč", "CZK"), ("Ft", "HUF"), ("lei", "RON"), ("лв", "BGN"), ("E£", "EGP"),
    ("€", "EUR"), ("£", ("GBP", "GIP", "FKP", "SHP")), ("₹", "INR"), ("₩", "KRW"), ("₱", "PHP"),
    ("฿", "THB"), ("₫", "VND"), ("₪", "ILS"), ("₺", "TRY"), ("TL", "TRY"), ("₴", "UAH"), ("₽", "RUB"),
    ("₦", "NGN"), ("₵", "GHS"), ("₸", "KZT"), ("₡", "CRC"), ("₲", "PYG"), ("￥", ("JPY", "CNY")),
    ("¥", ("JPY", "CNY")), ("kr.", ("DKK", "SEK", "NOK", "ISK")), ("kr", ("SEK", "NOK", "DKK", "ISK")),
    ("$", _DOLLARS), ("Fr.", "CHF"),
]
# One-letter signs are too easily part of a word or a model name, so they only count on a store
# whose own currency is written that way, and only right in front of the number.
_LETTERS = {"R": ("ZAR",), "Q": ("GTQ",), "L": ("HNL", "ALL", "LSL", "MDL", "SZL"),
            "K": ("ZMW", "MWK", "PGK", "MMK", "LAK"), "P": ("BWP",), "D": ("GMD",)}
_WORDLIKE = {"RM", "Rp", "Rs", "Rs.", "TL", "Ft", "zł", "Kč", "kr", "kr.", "lei", "лв", "Fr."}
_ISO = re.compile(r"(?<![A-Za-z])([A-Z]{3})(?![A-Za-z])")

# A number as stores print it: Indian grouping (1,23,456.00), groups of three split by comma, dot,
# space or apostrophe (1.299,00  1,299.00  1 299,00  1'299.50), or a plain number with optional cents.
_AMOUNT = re.compile(
    r"\d{1,3}(?:,\d{2})+,\d{3}(?:\.\d{1,2})?(?!\d)"
    r"|\d{1,3}(?:([.,' ’])\d{3})(?:\1\d{3})*(?:[.,]\d{1,3})?(?!\d)"
    r"|\d+(?:[.,]\d{1,3})?(?!\d)"
)
_SPACES = re.compile(r"[    ]")
_MARKS = re.compile(r"[‎‏؜]")   # invisible direction marks in Arabic-script prices


def _clean(text) -> str:
    return _MARKS.sub("", _SPACES.sub(" ", str(text or "")))


def _amount(token: str, currency: Optional[str]) -> Optional[float]:
    token = token.replace(" ", "").replace("'", "").replace("’", "")
    seps = [c for c in token if c in ".,"]
    if not seps:
        return float(token)
    last = max(token.rfind("."), token.rfind(","))
    tail = token[last + 1:]
    if len(set(seps)) == 2:
        decimal = token[last]          # both kinds present: the last one is the decimal point
    elif len(seps) > 1:
        decimal = None                 # 1.234.567 or 1,234,567: all thousands
    elif len(tail) == 3 and not (currency in THREE_DECIMALS and token[last] == "."):
        decimal = None                 # 1.299 or 1,299: a thousands separator (KWD 12.500 is not)
    else:
        decimal = token[last]
    if decimal is None:
        return float(re.sub(r"[.,]", "", token))
    whole = re.sub(r"[.,]", "", token[:last])
    return float(f"{whole or '0'}.{tail}")


def _alone(s: str, i: int, n: int) -> bool:
    """Is s[i:i+n] a word of its own ("RM1,299" yes, the R of "RTX" no)?"""
    before = s[i - 1] if i > 0 else " "
    after = s[i + n] if i + n < len(s) else " "
    return not before.isalpha() and not after.isalpha()


def _find_marker(s: str, fallback: str):
    for mark, cur in _MARKERS:
        start = 0
        while True:
            i = s.find(mark, start)
            if i < 0:
                break
            start = i + 1
            if mark in _WORDLIKE and not _alone(s, i, len(mark)):
                continue
            if isinstance(cur, tuple):
                return fallback if fallback in cur else cur[0]
            return cur
    for letter, curs in _LETTERS.items():
        if fallback in curs and re.search(rf"(?<![A-Za-z]){letter}\s?\d", s):
            return fallback
    m = _ISO.search(s)
    while m:
        if m.group(1) in _KNOWN_CODES:
            return m.group(1)
        m = _ISO.search(s, m.end())
    return None


def detect_currency(text, fallback: str = None) -> Optional[str]:
    return _find_marker(_clean(text), fallback) or fallback


def parse_money(text, fallback_currency: str = None):
    """(amount, currency) from a price string; (None, fallback) when there is no price in it."""
    s = _clean(text)
    cur = detect_currency(s, fallback_currency)
    m = _AMOUNT.search(s)
    if not m:
        return None, cur
    try:
        v = _amount(m.group(0), cur)
    except ValueError:
        return None, cur
    return (v if v > 0 else None), cur


def parse_price(text, fallback_currency: str = None) -> Optional[float]:
    return parse_money(text, fallback_currency)[0]


def parse_last_money(text, fallback_currency: str = None):
    """Like parse_money, but the last amount in the text: "Save 5% £495.36" is £495.36."""
    s = _clean(text)
    cur = detect_currency(s, fallback_currency)
    found = list(_AMOUNT.finditer(s))
    if not found:
        return None, cur
    try:
        v = _amount(found[-1].group(0), cur)
    except ValueError:
        return None, cur
    return (v if v > 0 else None), cur


def is_price_only(text, fallback: str = None) -> bool:
    """Is this short text just a price ("£3,200", "CHF1,100", "1.299 €") and nothing else?
    A bare number is not: on Facebook "5090" is a title."""
    s = _clean(text).strip()
    m = _AMOUNT.search(s)
    if not m:
        return False
    rest = (s[:m.start()] + s[m.end():]).strip()
    if not rest or len(rest) > 4:
        return False
    return _find_marker(rest, fallback) is not None and not re.search(r"\d", rest)


# ---------- formatting ----------
_SYMBOL = {"EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹", "KRW": "₩", "ILS": "₪", "PHP": "₱",
           "THB": "฿", "VND": "₫", "UAH": "₴", "NGN": "₦", "USD": "US$", "CAD": "CA$", "AUD": "A$",
           "NZD": "NZ$", "HKD": "HK$", "SGD": "S$", "MXN": "MX$", "BRL": "R$", "TWD": "NT$"}


def decimals(cur: str) -> int:
    return 0 if cur in ZERO_DECIMALS else 3 if cur in THREE_DECIMALS else 2


def fmt(amount, cur: str) -> str:
    """'€1,299.00', 'CA$949.99', '112,900 JPY' style: short, and never ambiguous about the currency."""
    if amount is None:
        return "no price"
    num = f"{amount:,.{decimals(cur)}f}"
    sym = _SYMBOL.get(cur)
    if sym and cur != "JPY":
        return f"{sym}{num}"
    return f"{num} {cur}"


# ---------- conversion ----------
class Rates:
    def __init__(self, path: str = RATES_FILE):
        self.path = path
        self._lock = threading.Lock()
        self.rates = {}          # currency -> units per US dollar
        self.fetched = 0.0
        self.source = ""
        self._last_try = 0.0
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d.get("rates"), dict) and d["rates"].get("USD"):
                self.rates, self.fetched, self.source = d["rates"], float(d.get("fetched") or 0), d.get("source", "")
        except Exception:
            pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"fetched": self.fetched, "source": self.source, "rates": self.rates}, f)
            os.replace(tmp, self.path)
        except Exception:
            pass    # a missing cache only costs one download at the next start

    def refresh(self, force: bool = False) -> bool:
        """Download fresh rates if the ones held are old. Returns True when usable rates are held."""
        with self._lock:
            now = time.time()
            if not force and self.rates and now - self.fetched < RATES_MAX_AGE:
                return True
            if not force and now - self._last_try < RATES_RETRY:
                return bool(self.rates)
            self._last_try = now
            for url, pick in RATE_SOURCES:
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "ItemHunter/1.0"})
                    with urllib.request.urlopen(req, timeout=12) as r:
                        rates = pick(json.loads(r.read().decode("utf-8")))
                    if rates and float(rates.get("USD", 0)) == 1.0:
                        self.rates = {k: float(v) for k, v in rates.items() if float(v) > 0}
                        self.fetched, self.source = now, url.split("/")[2]
                        self._save()
                        return True
                except Exception:
                    continue
            return bool(self.rates)    # stale rates beat none; a day-old rate is within a percent or two

    def convert(self, amount, src: str, dst: str) -> Optional[float]:
        if amount is None or not src or not dst:
            return None
        if src == dst:
            return float(amount)
        if not self.refresh():
            return None
        a, b = self.rates.get(src), self.rates.get(dst)
        if not a or not b:
            return None
        return round(float(amount) / a * b, decimals(dst))


rates = Rates()


def convert(amount, src, dst):
    return rates.convert(amount, src, dst)


# ISO codes the parser accepts when a price is written as "EUR 172,57" or "SEK4,400".
_KNOWN_CODES = {
    "USD", "CAD", "EUR", "GBP", "JPY", "CNY", "INR", "AUD", "NZD", "CHF", "SEK", "NOK", "DKK", "ISK",
    "PLN", "CZK", "HUF", "RON", "BGN", "TRY", "UAH", "RUB", "ILS", "AED", "SAR", "QAR", "KWD", "BHD",
    "OMR", "JOD", "EGP", "MAD", "TND", "ZAR", "NGN", "KES", "GHS", "BRL", "MXN", "ARS", "CLP", "COP",
    "PEN", "UYU", "HKD", "SGD", "MYR", "PHP", "THB", "IDR", "VND", "KRW", "TWD", "PKR", "BDT", "LKR",
    "NPR", "RSD", "BAM", "MKD", "ALL", "MDL", "GEL", "AMD", "AZN", "KZT", "UZS", "BYN", "LBP", "IQD",
    "DZD", "LYD", "XOF", "XAF", "XPF", "CRC", "GTQ", "HNL", "NIO", "DOP", "JMD", "TTD", "BOB", "PYG",
    "VES", "MOP", "MNT", "KHR", "LAK", "MMK", "ETB", "TZS", "UGX", "RWF", "ZMW", "MWK", "MZN", "AOA",
    "BWP", "NAD", "MUR", "SCR", "MVR", "FJD", "PGK",
}
