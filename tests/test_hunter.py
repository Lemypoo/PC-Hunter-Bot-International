"""Item Hunter's test suite. Run it with:  python tests/test_hunter.py

No test touches the network: the stores, the browser and the exchange rates are faked. Every check is
one line of plain English, so a failure says what behaviour broke rather than which assertion tripped.
"""
import json
import os
import sys
import tempfile
import threading
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hunter import countries, money, notify
import hunter.scheduler as schedmod
import hunter.sources as sourcesmod
import hunter.sources.amazon as amazon_mod
import hunter.store as storemod
from hunter.matching import matches, tokens_from_query
from hunter.money import fmt, is_price_only, parse_money
from hunter.scheduler import Scheduler
from hunter.sources import describe, sources_for
from hunter.sources.amazon import Amazon
from hunter.sources.base import BLOCK_BODY_RE, Listing, SourceError
from hunter.sources.ebay import Ebay
from hunter.sources.facebook import Facebook
from hunter.store import Store, suggest_excludes

notify.toast = lambda *a, **k: None
# fixed exchange rates, so nothing reaches the network and every conversion is predictable
money.rates.rates = {"USD": 1.0, "CAD": 1.40, "EUR": 0.90, "CHF": 0.80, "GBP": 0.75, "JPY": 150.0, "BGN": 1.76}
money.rates.fetched = time.time() + 10 ** 9
money.rates._save = lambda: None
sent = []
ok = True
paths = []
GB = {"notify": True, "region": "GB"}


def check(name, cond):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name)


def fresh(name):
    p = os.path.join(tempfile.gettempdir(), f"ihtest_{name}.json")
    for f in (p, p + ".tmp", p + ".bak"):
        if os.path.exists(f):
            os.remove(f)
    paths.append(p)
    return p


def new_store(name, region="GB"):
    st = Store(fresh(name))
    st.update_settings({"region": region})
    return st


def L(src, i, price, stock=True, title="AMD Ryzen 9 9950X3D CPU", currency="GBP", **kw):
    return Listing(source=src, source_name=src, id=i, title=title, url="u", price=price,
                   in_stock=stock, currency=currency, **kw)


def K(src, i, region="GB"):
    return f"{src}:{region}:{i}"


print("\n--- matching ---")
cpu = {"must": tokens_from_query("9950X3D"), "exclude": suggest_excludes("9950X3D")}
gpu = {"must": tokens_from_query("rtx 5090"), "exclude": suggest_excludes("rtx 5090")}
for it, title, price, extra, exp in [
    (cpu, "AMD Ryzen 9 9950X3D 16-Core/32Thread 4nm ZEN 5 CPU", 929.98, "", True),
    (cpu, "AMD Ryzen 9 9950X3D CPU + ASUS ROG STRIX X870E-H Motherboard", 2449.98, "", False),
    (cpu, "Mother Board Fit for JGINYUE B650M supports 9950X3D", 450.92, "", False),
    (cpu, "AMD Ryzen 9 9950X3D2 Dual Edition", 1229.98, "", False),
    (cpu, "AMD Ryzen 9 9950 X3D Processor", 900, "", True),
    (cpu, "Refurbished Dell Alienware Desktop 9950X3D", 3000, "Everyday Computing", False),
    (gpu, "ISO Nvidia RTX 5090", 123, "", False),
    (gpu, "(No GPU) MSI GeForce RTX 5090 Gaming Trio shroud", 240, "", False),
    (gpu, "ROG Strix SCAR 18 RTX 5090", 5999, "Gaming Laptops", False),
    (gpu, "Gigabyte Rtx 5090 Oc", 2700, "Parts Only", False),
    (gpu, "ASUS ROG Astral GeForce RTX 5090 OC", 3999, "Graphics Cards Brand New", True),
    (gpu, "NVIDIA GeForce RTX5090 32GB", 3999, "", True),        # written without the space
    (gpu, "NVIDIA GeForce RTX5080 16GB", 1999, "", False),
    (gpu, "PC i9 14900k/Asus Z790 Formula/2Tb NVMe G5 /48 RAM/1200W/ready for RTX 5090", 2598, "", False),
    (gpu, "Corsair HX1500i 1500W PSU ready for RTX 5090", 300, "", False),
    (gpu, "MSI GeForce RTX 5090 32G VENTUS 3X OC Graphics Card", 2699, "", True),
    (gpu, "HAVN CS9463 GPU Vertical Standing Kit White Sumitomo Electric RTX5090", 124, "", False),
    (gpu, "darkFlash FLOATRON F1 Micro-ATX PC case, RTX 5090 up to 425mm, 360mm radiator support", 404, "", False),
    (gpu, "Gigabyte AORUS GeForce RTX 5090 STEALTH ICE 32G Graphics Card - 32GB GDDR7, 512bit", 3799, "", True),
    (gpu, "ZOTAC GAMING GeForce RTX 5090 AMP Extreme INFINITY 32GB GDDR7", 3999, "Standard shipping", True),
]:
    check(f"{title[:46]!r:<48} -> {exp}", matches(it, title, price, extra)[0] == exp)


print("\n--- prices in every format ---")
for text, fallback, want in [
    ("£527.00", "GBP", (527.0, "GBP")), ("EUR 172,57", "EUR", (172.57, "EUR")),
    ("1.299,00 €", "EUR", (1299.0, "EUR")), ("1 299,00 €", "EUR", (1299.0, "EUR")),
    ("CHF1,100", "CHF", (1100.0, "CHF")), ("CHF 1'299.50", "CHF", (1299.5, "CHF")),
    ("¥112,900", "JPY", (112900.0, "JPY")), ("₹1,23,456.00", "INR", (123456.0, "INR")),
    ("C $1,411.37", "USD", (1411.37, "CAD")), ("US $1,229.98", "CAD", (1229.98, "USD")),
    ("$1,299.00", "MXN", (1299.0, "MXN")), ("BGN2,499", "EUR", (2499.0, "BGN")),
    ("R$ 5.999,00", "BRL", (5999.0, "BRL")), ("4.400 kr.", "DKK", (4400.0, "DKK")),
    ("KWD 185.500", "KWD", (185.5, "KWD")), ("‏SAR 3,299.00‏", "SAR", (3299.0, "SAR")),
    ("₪2,200", "ILS", (2200.0, "ILS")), ("Free", "USD", (None, "USD")),
]:
    check(f"{text!r:<28} reads as {want[0]} {want[1]}", parse_money(text, fallback) == want)
check("a price on its own is recognised whatever its currency",
      all(is_price_only(t, "EUR") for t in ("£3,200", "CHF1,100", "1.299 €", "SEK4,400", "CA$550", "₪2,200")))
check("titles and badges are not mistaken for prices",
      not any(is_price_only(t, "EUR") for t in ("5090", "RTX 5090", "Just listed", "£3,200\n£3,400", "32GB")))
check("prices are written unambiguously in alerts",
      (fmt(1299, "EUR"), fmt(112900, "JPY"), fmt(949.99, "CAD"), fmt(1100, "CHF"))
      == ("€1,299.00", "112,900 JPY", "CA$949.99", "1,100.00 CHF"))
check("a price from another currency converts through the dollar",
      money.convert(90, "EUR", "CHF") == 80.0 and money.convert(100, "CAD", "CAD") == 100.0)
check("a currency with no known rate gives no conversion rather than a wrong one",
      money.convert(100, "XYZ", "CAD") is None)


print("\n--- every country ---")
check("there are more than 230 countries, each with a name and a currency",
      len(countries.COUNTRIES) > 230 and all(v[0] and len(v[1]) == 3 for v in countries.COUNTRIES.values()))
check("every country Amazon sells to maps to a marketplace the app knows",
      all(countries.amazon_site(c) in countries.AMAZON_SITES
          for c in countries.COUNTRIES if c not in countries.EMBARGOED and countries.selectable(c)))
check("every country eBay sells to maps to an eBay site the app knows",
      all(countries.ebay_site(c) in countries.EBAY_SITES for c in countries.COUNTRIES
          if c not in countries.EMBARGOED and countries.selectable(c)))
check("every default Facebook city belongs to a real country", set(countries.FACEBOOK_CITY) <= set(countries.COUNTRIES))
check("countries under sanctions get neither Amazon nor eBay",
      all(countries.amazon_site(c) is None and countries.ebay_site(c) is None for c in countries.EMBARGOED))
check("Germany gets Amazon.de, eBay.de and Facebook",
      [s["name"] for s in describe({"fb_city": "berlin"}, "DE")] == ["Amazon.de", "eBay.de", "Facebook Marketplace"])
check("Canada and the US are left to the Canada and US edition",
      not countries.selectable("CA") and not countries.selectable("US")
      and not {"CA", "US"} & {c["code"] for c in countries.listing()} and describe({}, "US") == [])
check("no Canadian or US store is left in this edition",
      sorted(sourcesmod.REGISTRY) == ["amazon", "ebay", "facebook"])
check("Japan has no Facebook Marketplace", "facebook" not in [s["key"] for s in describe({}, "JP")])
check("Switzerland is served by Amazon.de, with a note saying so",
      describe({}, "CH")[0]["name"] == "Amazon.de" and "Switzerland" in describe({}, "CH")[0]["note"])
check("inside the EU the note does not warn about import fees",
      "import" not in describe({}, "AT")[0]["note"] and "import" in describe({}, "CH")[0]["note"])
check("Facebook sits out until a city is set",
      "facebook" not in [s.key for s in sources_for({"region": "DE", "fb_city": ""})]
      and "facebook" in [s.key for s in sources_for({"region": "DE", "fb_city": "berlin"})])
check("the browser always presents an English locale it can use",
      all(countries.browser_locale(c).startswith("en-") for c in countries.COUNTRIES))


print("\n--- Amazon: which page came back ---")
class AmazonPage:
    def __init__(self, pages):
        self.pages, self.cur, self.urls = list(pages), None, []

    def goto(self, url, **k):
        self.urls.append(url)
        self.cur = self.pages.pop(0)

    def title(self):
        return "Amazon.ca"

    def wait_for_selector(self, *a, **k):
        pass

    def wait_for_timeout(self, *a, **k):
        pass

    def evaluate(self, js, arg=None):
        state, cards = self.cur
        if "captcha:" in js:
            return state
        if "document.body" in js:
            return "Amazon.ca results"
        return cards


def card(asin, price, sponsored=False, offers=None, title="AMD Ryzen 9 9950X3D 16-Core Processor", whole="", frac=""):
    return {"id": asin, "title": title, "url": "", "price": price, "whole": whole, "frac": frac, "was": "",
            "offers": offers, "sponsored": sponsored, "unavailable": False, "used": False}


OKST = lambda n: {"cards": n, "captcha": False, "noResults": False}
amazon_mod._resale_cache.clear()

try:
    Amazon({"include_used": False}).search(AmazonPage([({"cards": 0, "captcha": True, "noResults": False}, [])]), "q", "GB")
    check("a robot check is reported as a block", False)
except SourceError as e:
    check("a robot check is reported as a block", "blocked" in str(e).lower())
try:
    Amazon({"include_used": False}).search(AmazonPage([({"cards": 0, "captcha": False, "noResults": False}, [])]), "q", "GB")
    check("a page with no result cards is an error, not an empty market", False)
except SourceError as e:
    check("a page with no result cards is an error, not an empty market", "no search results" in str(e))
check("a real 'No results for' page is quietly empty",
      Amazon({"include_used": False}).search(AmazonPage([({"cards": 0, "captcha": False, "noResults": True}, [])]), "zz", "GB") == [])
out = Amazon({"include_used": False}).search(
    AmazonPage([(OKST(2), [card("B01", "£949.99", sponsored=True), card("B01", "£929.98")])]), "q", "GB")
check("one ASIN listed twice on a page becomes one row at the cheaper price",
      len(out) == 1 and out[0].price == 929.98)
check("Amazon's robot-check wording is recognised",
      bool(BLOCK_BODY_RE.search("Enter the characters you see below. Sorry, we just need to make sure you're not a robot.")))

amazon_mod._resale_cache.clear()
p1 = AmazonPage([(OKST(1), [card("B01", "£929.98")]),
                 (OKST(1), [card("B02", "", offers={"text": "£700.00 ", "count": "1", "kind": "used"})])])
Amazon({"include_used": True}).search(p1, "9950x3d", "GB")
p2 = AmazonPage([(OKST(1), [card("B01", "£929.98")])])
out2 = Amazon({"include_used": True}).search(p2, "9950X3D", "GB")
check("the Resale page is fetched once then reused, halving Amazon traffic",
      len(p1.urls) == 2 and len(p2.urls) == 1 and any(l.id == "B02:used" for l in out2))
amazon_mod._resale_cache.clear()
out = Amazon({"include_used": True}).search(
    AmazonPage([(OKST(1), [card("B01", "£929.98")]), ({"cards": 0, "captcha": False, "noResults": False}, [])]), "x1", "GB")
check("a half-loaded Resale page keeps the main results", [l.id for l in out] == ["B01"])
amazon_mod._resale_cache.clear()
try:
    Amazon({"include_used": True}).search(
        AmazonPage([(OKST(1), [card("B01", "£929.98")]), ({"cards": 0, "captcha": True, "noResults": False}, [])]), "x2", "GB")
    check("a robot check on the Resale page still backs Amazon off", False)
except SourceError as e:
    check("a robot check on the Resale page still backs Amazon off", "blocked" in str(e).lower())

# the shapes seen on Amazon.co.uk, .de and .co.jp in September 2026
amazon_mod._resale_cache.clear()
uk = AmazonPage([(OKST(1), [card("B0DVZSG8D5", "£527.00", whole="527.", frac="00",
                                 offers={"text": "£495.36", "count": "12", "kind": "used & new"})]),
                 (OKST(1), [card("B0BTRH9MNS", "", offers={"text": "€548.88 ", "count": "1", "kind": "used"})])])
got = {l.id: l for l in Amazon({"include_used": True}).search(uk, "9950x3d", "GB")}
check("Amazon.co.uk: the new price, in pounds, from its whole and fraction parts",
      got["B0DVZSG8D5"].price == 527.0 and got["B0DVZSG8D5"].currency == "GBP")
check("'12+ used & new offers' style lines become a used row", got["B0DVZSG8D5:used"].price == 495.36)
check("the page is asked for in English", "language=en_GB" in uk.urls[0] and "amazon.co.uk" in uk.urls[0])
jp = AmazonPage([(OKST(1), [card("B0D6NNRBGP", "¥112,900", whole="112,900", title="AMD Ryzen 9 9950X3D")])])
got = Amazon({"include_used": True}).search(jp, "9950x3d", "JP")
check("Amazon.co.jp: yen with no cents, and no Resale page asked for where it does not exist",
      got[0].price == 112900 and got[0].currency == "JPY" and len(jp.urls) == 1)
check("listings carry the country they were found under", got[0].region == "JP" and got[0].key == "amazon:JP:B0D6NNRBGP")
ke = AmazonPage([(OKST(1), [card("B0F1", "KES 258,430.00", whole="258,430", frac="00", title="INNO3D GeForce RTX 5090 X3 OC",
                                 offers={"text": "KES 240,000.00", "count": "3", "kind": "used & new"})])])
got = {l.id: l for l in Amazon({"include_used": False}).search(ke, "rtx 5090", "KE")}
check("Amazon.com showing a Kenyan visitor shillings is read as shillings, not as dollars",
      "amazon.com" in ke.urls[0] and got["B0F1"].price == 258430.0 and got["B0F1"].currency == "KES")
us = AmazonPage([(OKST(1), [card("B0F2", "$1,999.99", whole="1,999", frac="99")])])
got = Amazon({"include_used": False}).search(us, "rtx 5090", "AR")
check("...while a plain dollar sign there still means US dollars", got[0].currency == "USD" and got[0].price == 1999.99)


print("\n--- eBay and Facebook abroad ---")
class RowsPage:
    """A search page that has loaded fine and holds these rows."""
    def __init__(self, rows, url="", title="eBay"):
        self.rows, self.url, self._title, self.urls = rows, url, title, []

    def goto(self, url, **k):
        self.urls.append(url)

    def title(self):
        return self._title

    def wait_for_selector(self, *a, **k):
        pass

    def wait_for_timeout(self, *a, **k):
        pass

    def evaluate(self, js, arg=None):
        if "document.body" in js and "innerText" in js and "map" not in js:
            return "x" * 700
        return self.rows


de_rows = [
    {"id": "1", "title": "Shop on eBay", "url": "https://www.ebay.de/itm/123456", "price": "$20.00", "condition": "Brand New", "rows": []},
    {"id": "2", "title": "GIGABYTE RTX 5090 Aorus Master ICE 32GB No Core", "url": "", "price": "EUR 172,57",
     "condition": "Nur Ersatzteile | Privat", "rows": ["EUR 172,57", "Gratis Lieferung", "aus Kanada"]},
    {"id": "3", "title": "MSI GeForce RTX 5090 Ventus 3X OC 32GB", "url": "", "price": "EUR 2.349,00",
     "condition": "Neu | Gewerblich", "rows": ["EUR 2.349,00", "Sofort-Kaufen", "Kostenloser Versand", "aus Deutschland"]},
]
page = RowsPage(de_rows)
got = Ebay({}).search(page, "rtx 5090", "DE")
check("eBay.de: German prices read correctly, in euros", [(l.id, l.price, l.currency) for l in got] == [("3", 2349.0, "EUR")])
check("eBay.de: 'Nur Ersatzteile' (parts only) and placeholder cards are left out", len(got) == 1)
check("eBay.de: the German 'aus Deutschland' line gives the location", got[0].location == "Deutschland")
check("eBay.de is the site searched from Germany", page.urls[0].startswith("https://www.ebay.de/sch/"))

fb_rows = [{"href": "/marketplace/item/111/", "spans": ["£3,200\n£3,400", "£3,200", "£3,400", "MSI RTX 5090 32GB Ventus OC",
                                                        "Beckenham, Bromley, United Kingdom"]},
           {"href": "/marketplace/item/222/", "spans": ["CA$550", "Just listed", "RTX 5090", "Nanaimo, BC"]}]
got = {l.id: l for l in Facebook({"fb_city": "london"}).search(
    RowsPage(fb_rows, url="https://www.facebook.com/marketplace/london/search/?query=x"), "rtx 5090", "GB")}
check("Facebook London: pounds read, and the old price kept as the 'was' price",
      got["111"].price == 3200 and got["111"].currency == "GBP" and got["111"].was_price == 3400)
check("Facebook: a listing priced in another currency keeps that currency", got["222"].currency == "CAD")
check("Facebook: a title that is only a model number is still the title", got["222"].title == "RTX 5090")
try:
    Facebook({"fb_city": "notarealcity"}).search(
        RowsPage(fb_rows, url="https://www.facebook.com/marketplace/category/search/?query=x"), "rtx 5090", "GB")
    check("a city Facebook does not know is reported, not silently swapped for another", False)
except SourceError as e:
    check("a city Facebook does not know is reported, not silently swapped for another",
          "does not recognise" in str(e) and "blocked" not in str(e))


print("\n--- other stores ---")
class FBPage:
    url = "https://www.facebook.com/marketplace/london/search/?query=x"

    def goto(self, *a, **k):
        pass

    def wait_for_selector(self, *a, **k):
        pass

    def wait_for_timeout(self, *a, **k):
        pass

    def evaluate(self, js, arg=None):
        return [{"href": "/marketplace/item/111/", "spans": ["£550", "Just listed", "Ryzen 7 9800X3D", "Croydon, London"]}]


fb = {l.id: l for l in Facebook({"fb_city": "london"}).search(FBPage(), "9800x3d", "GB")}
check("Facebook's 'Just listed' badge is not mistaken for the title", fb["111"].title == "Ryzen 7 9800X3D")


class FBSearch:
    """Facebook as it behaved in September 2026: nothing for "9950X3D", listings for "cpu 9950X3D"."""
    def __init__(self):
        self.urls, self.url = [], ""

    def goto(self, url, **k):
        self.urls.append(url)
        self.url = url

    def wait_for_selector(self, *a, **k):
        pass

    def wait_for_timeout(self, *a, **k):
        pass

    def evaluate(self, js, arg=None):
        if "map" not in js:
            return 'No listings found for "9950X3D" within 65 kilometres. Try a new search.'
        if "query=cpu+9950X3D" in self.url:
            return [{"href": "/marketplace/item/333/", "spans": ["£460", "AMD Ryzen 9 9950X3D 16-Core Processor", "Richmond, London"]}]
        return []


fbp = FBSearch()
got = Facebook({"fb_city": "london"}).search(fbp, "9950X3D", "GB")
check("Facebook's empty answer for a bare model number is retried as 'cpu 9950X3D', which finds it",
      [l.price for l in got] == [460] and len(fbp.urls) == 2 and "query=cpu+9950X3D" in fbp.urls[1])
fbp2 = FBSearch()
Facebook({"fb_city": "london"}).search(fbp2, "9950X3D", "GB")
check("...and the wording that works is used straight away next time", fbp2.urls == [fbp.urls[1]])
fbp3 = FBSearch()
check("a search that is not a PC part is not retried",
      Facebook({"fb_city": "london"}).search(fbp3, "desk lamp", "GB") == [] and len(fbp3.urls) == 1)


print("\n--- ingest: events, alerts, churn ---")
notify.toast = lambda t, m, u=None, wait=False: sent.append(t)
store = new_store("ingest")
sc = Scheduler(store)
item = store.add_item("9950X3D")


class AZ:
    key = "amazon"


class EB:
    key = "ebay"


S = GB
sc.ingest(item, AZ, [L("amazon", "A", 929.98), L("amazon", "B", 999.0, False)], S)
check("the first read of a store is a baseline: no feed entries, no alerts", store.events == [] and sent == [])
sc.ingest(item, AZ, [L("amazon", "A", 899.0), L("amazon", "B", 999.0, False)], S)
check("a price drop raises one feed entry and one alert",
      [e["type"] for e in store.events] == ["drop"] and len(sent) == 1)
sc.ingest(item, AZ, [L("amazon", "A", 899.0), L("amazon", "B", 1100.0, True)], S)
check("a restock far above the best price stays out of the feed", len(store.events) == 1)
recs = store.listings[item["id"]]
sc.ingest(item, EB, [L("ebay", "E", 10.0), L("ebay", "F", 850.0)], S)
check("a placeholder price is flagged and the real one is not",
      recs[K("ebay", "E")]["suspect"] and not recs[K("ebay", "F")]["suspect"])
check("the best price ignores the placeholder", sc._best_price(recs, set()) == 850.0)
for _ in range(5):
    sc.ingest(item, AZ, [], S)
check("a store answering with nothing keeps the listings it had",
      recs[K("amazon", "A")]["active"] and recs[K("amazon", "A")]["misses"] == 0)
recs[K("amazon", "A")]["last_seen"] -= 7 * 3600
sc.ingest(item, AZ, [], S)
check("...but a listing unseen for six hours expires", not recs[K("amazon", "A")]["active"])
recs[K("amazon", "A")].update(active=True, last_seen=time.time(), misses=0)
for _ in range(5):
    sc.ingest(item, AZ, [L("amazon", "B", 1100.0)], S)
check("a listing missing for a few minutes is not declared gone (result-order churn)", recs[K("amazon", "A")]["active"])
recs[K("amazon", "A")]["last_seen"] -= 3600
sc.ingest(item, AZ, [L("amazon", "B", 1100.0)], S)
check("...it is declared gone after half an hour", not recs[K("amazon", "A")]["active"])
store.clear_events()
sc.ingest(item, AZ, [L("amazon", "A", 700.0), L("amazon", "A", 750.0)], S)
check("the same listing twice in one read gives one price, not a drop and a rise",
      recs[K("amazon", "A")]["price"] == 700.0 and len([e for e in store.events if e["key"] == K("amazon", "A")]) == 1)
sent.clear()
store.clear_events()
sc.ingest(item, EB, [L("ebay", f"N{i}", 600 + i) for i in range(8)], S)
check("eight new cheap listings give eight feed entries but at most three alerts",
      sum(e["type"] == "new" for e in store.events) == 8 and len(sent) == 3)

st_r = new_store("restock")
sc_r = Scheduler(st_r)
it_r = st_r.add_item("9950X3D")
sc_r.ingest(it_r, AZ, [L("amazon", "A", 929.98, False)], {"notify": False, "region": "GB"})
sc_r.ingest(it_r, AZ, [L("amazon", "A", 929.98, True)], {"notify": False, "region": "GB"})
check("a listing coming back in stock raises a restock entry", [e["type"] for e in st_r.events] == ["restock"])

st_f = new_store("floor")
sc_f = Scheduler(st_f)
it_f = st_f.add_item("9950X3D")
prices = [929.98, 999.99, 1890, 2406, 2682, 2748, 2838, 4390, 4432, 4479]
sc_f.ingest(it_f, AZ, [L("amazon", f"A{i}", p) for i, p in enumerate(prices)], {"notify": False, "region": "GB"})
sc_f.ingest(it_f, EB, [L("ebay", "E1", 800.0), L("ebay", "E2", 10.0)], {"notify": False, "region": "GB"})
rf = st_f.listings[it_f["id"]]
check("a real bargain survives a listing page full of overpriced resellers", not rf[K("ebay", "E1")]["suspect"])
check("a one-dollar placeholder does not", rf[K("ebay", "E2")]["suspect"])


print("\n--- several currencies and countries ---")
st_x = new_store("currency", region="CH")
sc_x = Scheduler(st_x)
it_x = st_x.add_item("9950X3D")
CH = {"notify": True, "region": "CH"}
sc_x.ingest(it_x, AZ, [L("amazon", "D1", 900.0, currency="EUR")], CH)          # Amazon.de, in euros
sc_x.ingest(it_x, EB, [L("ebay", "C1", 760.0, currency="CHF")], CH)            # eBay.ch, in francs
rx = st_x.listings[it_x["id"]]
check("a listing in euros is compared in Swiss francs", rx[K("amazon", "D1", "CH")]["home_price"] == 800.0)
check("...so 760 francs beats 900 euros (800 francs)", sc_x._best_price(rx, set()) == 760.0)
sent.clear()
st_x.clear_events()
sc_x.ingest(it_x, AZ, [L("amazon", "D1", 820.0, currency="EUR")], CH)          # 738 francs: a new best
check("a drop abroad that beats the best price at home alerts, and says both prices",
      len(sent) == 1 and st_x.events[0]["home_price"] == 728.89 and st_x.events[0]["currency"] == "EUR")
title, body = notify.format_event(st_x.events[0])
check("the alert shows the euro price and what it comes to in francs",
      "€900.00 -> €820.00 (about 728.89 CHF)" in body)
st_x.clear_events()
sent.clear()
sc_x.ingest(it_x, EB, [L("ebay", "C1", 700.0, currency="EUR")], CH)            # same listing, now shown in euros
check("a listing that switches currency is not reported as a price drop",
      st_x.events == [] and rx[K("ebay", "C1", "CH")]["currency"] == "EUR")
st_x.update_item(it_x["id"], {"target_price": 1000})
real_rates = money.rates.rates
money.rates.rates = {"USD": 1.0, "CHF": 0.8}       # no rate for euros at all
money.rates._last_try = time.time()
sc_x.ingest(it_x, AZ, [L("amazon", "D1", 500.0, currency="EUR")], CH)
check("with no exchange rate, a foreign price raises no alert and cannot be the best price",
      st_x.events == [] and rx[K("amazon", "D1", "CH")]["home_price"] is None
      and sc_x._best_price(rx, set()) != 500.0)
money.rates.rates = real_rates

st_m = new_store("move")
sc_m = Scheduler(st_m)
it_m = st_m.add_item("9950X3D")
sc_m.ingest(it_m, AZ, [L("amazon", "A", 529.98)], GB)
sc_m.ingest(it_m, AZ, [L("amazon", "A", 499.00)], GB)
st_m.update_settings({"region": "DE"})
st_m.clear_events()
sent.clear()
DE = {"notify": True, "region": "DE", "sources": {}}
sc_m.ingest(it_m, AZ, [L("amazon", "A", 549.0, currency="EUR"), L("amazon", "B", 599.0, currency="EUR")], DE)
check("after moving from the UK to Germany, the first Amazon.de read is a baseline, not a flood of alerts",
      st_m.events == [] and sent == [])
recs_m = st_m.listings[it_m["id"]]
check("the British and German copies of one product are kept apart",
      recs_m[K("amazon", "A", "GB")]["currency"] == "GBP" and recs_m[K("amazon", "A", "DE")]["currency"] == "EUR")
import app as appmod
appmod.store, appmod.sched = st_m, sc_m
card_m = next(i for i in appmod.build_state()["items"] if i["id"] == it_m["id"])
check("the page shows only the current country's listings", {r["region"] for r in card_m["listings"]} == {"DE"})
check("...and the page is told the country and its currency",
      appmod.build_state()["country"] == {"code": "DE", "name": "Germany", "currency": "EUR"})

st_c = new_store("city", region="GB")
check("a new country brings its Facebook city when the old one was only the default",
      st_c.settings["fb_city"] == "london"
      and st_c.update_settings({"region": "FR"})["fb_city"] == "paris")
st_c.update_settings({"fb_city": "Lyon"})
check("...but a city the user typed stays put", st_c.update_settings({"region": "DE"})["fb_city"] == "lyon")
check("an unknown country code is refused", st_c.update_settings({"region": "ZZ"})["region"] == "DE")
check("so are Canada and the US, which the other edition covers", st_c.update_settings({"region": "US"})["region"] == "DE")

real_detect = countries.detect
countries.detect = lambda: "CA"            # a computer whose Windows region is Canada
st_ca = Store(fresh("pc_in_canada"))
check("on a computer set to Canada, the first start picks the UK rather than a country this edition lacks",
      st_ca.settings["region"] == "GB" and st_ca.settings["fb_city"] == "london")
appmod.store = st_ca
check("...and the page points to the Canada and US edition",
      (appmod.build_state()["other_edition"] or {}).get("url") == "https://github.com/Lemypoo/PC-Hunter-Bot-US-CANADA")
st_ca.update_settings({"region": "FR"})
check("...until a country is picked in Settings", appmod.build_state()["other_edition"] is None)
countries.detect = lambda: "DE"
check("a computer set to Germany starts on Germany, with no pointer elsewhere",
      Store(fresh("pc_in_germany")).settings["region"] == "DE")
countries.detect = real_detect
appmod.store = st_m


print("\n--- a state file from the Canada and US edition ---")
legacy_path = fresh("legacy")
legacy = {
    "settings": {"region": "CA", "fb_city": "vancouver", "push": {"enabled": True, "topic": "t", "server": "https://ntfy.sh"}},
    "items": [{"id": "i1", "query": "9950X3D", "name": "9950X3D", "must": ["9950x3d"], "exclude": [],
               "hidden": ["amazon:B0H"], "seen_sources": {"amazon": True}, "sources": None, "paused": False}],
    "listings": {"i1": {
        "amazon:B01": {"key": "amazon:B01", "source": "amazon", "source_name": "Amazon.ca", "id": "B01",
                       "title": "AMD Ryzen 9 9950X3D", "url": "u", "price": 929.98, "currency": "CAD",
                       "in_stock": True, "active": True, "last_seen": time.time(), "history": [], "lowest": 929.98},
        "amazon:B0H": {"key": "amazon:B0H", "source": "amazon", "source_name": "Amazon.ca", "id": "B0H",
                       "title": "AMD Ryzen 9 9950X3D", "url": "u", "price": 950.0, "currency": "CAD",
                       "in_stock": True, "active": True, "last_seen": time.time(), "history": [], "lowest": 950.0}}},
    "events": [{"key": "amazon:B01", "item_id": "i1", "type": "drop", "price": 929.98}],
}
json.dump(legacy, open(legacy_path, "w", encoding="utf-8"))
moved = Store(legacy_path)
lr = moved.listings["i1"]
check("its Canadian listings are filed under Canada, out of sight, instead of being read as local prices",
      set(lr) == {"amazon:CA:B01", "amazon:CA:B0H"} and lr["amazon:CA:B01"]["currency"] == "CAD")
check("the country moves to one this edition covers, with that country's Facebook city",
      moved.settings["region"] != "CA" and countries.selectable(moved.settings["region"])
      and moved.settings["fb_city"] == countries.FACEBOOK_CITY.get(moved.settings["region"], ""))
check("settings such as the phone topic come across untouched", moved.settings["push"]["topic"] == "t")
appmod.store = moved
check("none of the Canadian listings show on the page",
      all(not i["listings"] for i in appmod.build_state()["items"]))
appmod.store = st_m


print("\n--- the store file ---")
st = new_store("store")
st.add_item("rtx 4090")
for q in ("RTX 4090", "  rtx   4090 ", "Rtx-4090"):
    try:
        st.add_item(q)
        check(f"a duplicate of {q!r} is refused", False)
    except ValueError as e:
        check(f"a duplicate of {q!r} is refused", "Already hunting" in str(e))
other = st.add_item("rtx 5090")
try:
    st.update_item(other["id"], {"query": "RTX 4090", "name": "renamed"})
    check("editing a card into a duplicate is refused", False)
except ValueError:
    check("editing a card into a duplicate is refused, leaving the card untouched",
          st.get_item(other["id"])["name"] == "rtx 5090")
check("the checking speed only accepts known values",
      st.update_settings({"speed": "fast"})["speed"] == "fast"
      and st.update_settings({"speed": "ludicrous"})["speed"] == "fast")
check("the number of stores checked at once is held between 1 and 4",
      st.update_settings({"workers": 9})["workers"] == 4 and st.update_settings({"workers": 0})["workers"] == 1)

itp = st.add_item("9800X3D")
recs = st.listings[itp["id"]]
old = time.time() - 20 * 86400
recs["x:old"] = {"key": "x:old", "source": "amazon", "active": False, "last_seen": old, "price": 1, "region": "GB"}
recs["x:gone_recently"] = {"key": "x:gone_recently", "source": "amazon", "active": False, "last_seen": time.time(), "price": 1, "region": "GB"}
recs["x:live"] = {"key": "x:live", "source": "amazon", "active": True, "last_seen": old, "price": 1, "region": "GB"}
st.get_item(itp["id"])["hidden"] = ["x:old", "x:live"]
n = st.prune()
check("listings gone a fortnight are forgotten, recent and live ones kept",
      n == 1 and "x:old" not in recs and "x:gone_recently" in recs and "x:live" in recs)
check("a hide-mark for a forgotten listing is cleaned up", st.get_item(itp["id"])["hidden"] == ["x:live"])

st.save()
check("saving keeps the previous version as a backup", os.path.exists(st.path + ".bak"))
open(st.path, "wb").write(b"\x00" * 4000)          # exactly how the power cut corrupted it
recovered = Store(st.path)
check("a state file destroyed by a power cut is recovered from the backup",
      [i["name"] for i in recovered.items] == [i["name"] for i in st.items])
check("...and the wrecked file is kept aside rather than deleted",
      any(f.startswith(os.path.basename(st.path) + ".corrupt-") for f in os.listdir(os.path.dirname(st.path))))
src = open(os.path.join(os.path.dirname(__file__), "..", "hunter", "store.py"), encoding="utf-8").read()
check("the state file is flushed to disk before it replaces the old one", "os.fsync(f.fileno())" in src)

real_replace = os.replace
tries = {"n": 0}


def locked_twice(a, b):
    tries["n"] += 1
    if tries["n"] <= 2:
        raise PermissionError(13, "file in use")
    return real_replace(a, b)


storemod.os.replace = locked_twice
real_sleep, storemod.time.sleep = time.sleep, lambda s: None
st.save()
storemod.os.replace, storemod.time.sleep = real_replace, real_sleep
check("saving retries when Windows briefly locks the file", tries["n"] >= 3)


print("\n--- checking: back-off and honesty ---")
class FakePage:
    def close(self):
        pass


class FakeBrowser:
    def __init__(self, channel="msedge", region="GB", state_file=""):
        self.channel, self.region = channel, region
        self._ctx = object()
        self.restarts = 0

    @staticmethod
    def state_file_for(name):
        return ""

    def start(self):
        self._ctx = object()

    def page(self):
        return FakePage()

    def restart(self):
        self.restarts += 1

    def stop(self):
        pass


def source(key, behaviour, gap=0, every=60):
    class Src:
        min_gap = gap
        interval = every

        def __init__(self, settings):
            pass

        def display_name(self, r):
            return key

        def search(self, page, q, r):
            return behaviour(q)
    Src.key = key
    return Src


def boom(q):
    raise TimeoutError("Page.goto: Timeout 45000ms exceeded")


real_uniform = schedmod.random.uniform
schedmod.random.uniform = lambda a, b: 0    # skip run_cycle's polite pause between stores
st2 = new_store("backoff")
sc2 = Scheduler(st2)
sc2.browser = FakeBrowser()
it2 = st2.add_item("9950X3D")
hits = []
schedmod.sources_for = lambda s: [source("amazon", lambda q: hits.append(q) or boom(q))(s)]
sc2.run_cycle(None)
check("one failure alone does not back a store off", "amazon" not in sc2._backoff and len(hits) == 1)
sc2.run_cycle(None)
check("a second failure in a row does (the old code retried forever)", sc2._backoff.get("amazon", 0) > time.time() + 100)
sc2.run_cycle(None)
check("a backed-off store is not contacted", len(hits) == 2)
check("the error says when the store will be tried again",
      "Trying this store again at" in sc2.status_snapshot()["errors"]["amazon"]["msg"])
check("a card is not marked checked when every store failed", st2.get_item(it2["id"])["last_checked"] is None)
sc2._backoff.clear()
schedmod.sources_for = lambda s: [source("amazon", lambda q: [])(s)]
sc2.run_cycle(None)
check("a success clears the failure count, the pause and the error",
      "amazon" not in sc2._fails and "amazon" not in sc2._backoff and "amazon" not in sc2.status_snapshot()["errors"])
check("...and marks the card checked", st2.get_item(it2["id"])["last_checked"] is not None)
sc2._set_error("ebay", "blocked", "x")
sc2.run_cycle(None)
check("an error from a store no longer switched on disappears", "ebay" not in sc2.status_snapshot()["errors"])


print("\n--- checking: several stores at once ---")
st3 = new_store("parallel")
for q in ("RTX 5090", "9950X3D", "RTX 5080"):
    st3.add_item(q)
sc3 = Scheduler(st3)
spans = []
spans_lock = threading.Lock()


def timed(key):
    def run(q):
        start = time.time()
        time.sleep(0.25)          # a store takes a moment to answer
        with spans_lock:
            spans.append((key, q, start, time.time()))
        return []
    return run


schedmod.random.uniform = real_uniform     # the cadence jitter needs to be real again
schedmod.Browser = FakeBrowser
schedmod.sources_for = lambda s: [source("ebay", timed("ebay"), gap=0, every=1)(s),
                                  source("amazon", timed("amazon"), gap=0, every=30)(s)]
st3.update_settings({"workers": 2, "speed": "normal"})
sc3.start()
time.sleep(4)
sc3.stop()
with spans_lock:
    runs = list(spans)
by_store = {}
for key, q, a, b in runs:
    by_store.setdefault(key, []).append((a, b))
overlap_same = any(a1 < b2 and a2 < b1 for key, times in by_store.items()
                   for i, (a1, b1) in enumerate(times) for (a2, b2) in times[i + 1:])
amz = by_store.get("amazon", [])
bby = by_store.get("ebay", [])
overlap_diff = any(a1 < b2 and a2 < b1 for (a1, b1) in amz for (a2, b2) in bby)
check("both stores were checked", len(amz) >= 1 and len(bby) >= 3)
check("two stores really are checked at the same time", overlap_diff)
check("but one store is never asked twice at the same moment", not overlap_same)
fast_per_item = {}
for key, q, a, b in runs:
    if key == "ebay":
        fast_per_item.setdefault(q, []).append(a)
check("the quick store swept every item in four seconds", len(fast_per_item) == 3)
check("the slow store did not run away with itself", len(amz) <= 3)
gaps = [round(t2 - t1, 2) for times in fast_per_item.values() for t1, t2 in zip(sorted(times), sorted(times)[1:])]
check("an item is not re-checked at one store faster than that store's own clock",
      all(g >= 0.85 for g in gaps) if gaps else True)

st3.update_settings({"speed": "relaxed"})
check("the speed setting scales a store's clock",
      abs(schedmod.SPEED["relaxed"] - 2.0) < 1e-9 and schedmod.SPEED["fast"] < schedmod.SPEED["normal"])

sc4 = Scheduler(st3)
sc4._due[(st3.items[0]["id"], "amazon")] = time.time() + 9999
sc4.request(st3.items[0]["id"])
check("pressing Check now makes an item due immediately",
      sc4._due[(st3.items[0]["id"], "amazon")] == 0.0)
sc4._due[("ghost-item", "amazon")] = 0.0
schedmod.sources_for = lambda s: [source("amazon", lambda q: [])(s)]
sc4._claim()
check("jobs for a removed item are forgotten", ("ghost-item", "amazon") not in sc4._due)
st3.items[0]["paused"] = True
picked = [sc4._claim() for _ in range(3)]
check("a paused item is never picked up", all(j is None or j[0]["id"] != st3.items[0]["id"] for j in picked))
schedmod.sources_for = sourcesmod.sources_for


print("\n--- the web app ---")
st5 = new_store("web")
sc5 = Scheduler(st5)
appmod.store, appmod.sched = st5, sc5
st5.add_item("RTX 5090")
stop = threading.Event()


def churn():
    i = 0
    while not stop.is_set():
        i += 1
        sc5._set_error(f"k{i % 40}", "x" * 40, "RTX 5090")
        sc5._clear_error(f"k{(i + 20) % 40}")
        with sc5._lock:
            sc5._due[(f"i{i % 30}", "amazon")] = time.time()
            sc5._busy[f"w{i % 3}"] = "checking"
            sc5._busy.pop(f"w{(i + 1) % 3}", None)


schedmod.print = lambda *a, **k: None
t = threading.Thread(target=churn, daemon=True)
t.start()
client = appmod.app.test_client()
bad = sum(1 for _ in range(400) if client.get("/api/state").status_code != 200)
stop.set()
t.join()
check("the page's state request never fails while the checkers write status", bad == 0)
r = client.post("/api/items", json={"query": "rtx 5090"})
check("adding a duplicate answers 409 with a readable message",
      r.status_code == 409 and "Already hunting" in r.get_json()["error"])
first = client.post("/api/items", json={"query": "9950X3D"}).get_json()
check("editing into a duplicate answers 409, not a server error",
      client.patch(f"/api/items/{first['id']}", json={"query": "RTX 5090"}).status_code == 409)
state = client.get("/api/state").get_json()
check("the page is told how often each store is checked",
      state["cadence"]["ebay"] < state["cadence"]["amazon"])
cl = client.get("/api/countries").get_json()
check("the country list reaches the page, sorted by name with accents filed as plain letters",
      len(cl) > 230 and [c["name"] for c in cl] == sorted((c["name"] for c in cl), key=countries.sort_key)
      and cl[0]["name"] == "Afghanistan" and cl[1]["name"] == "Åland Islands")
r = client.get("/api/stores?region=GB").get_json()
check("the Settings dialog can ask which stores serve another country",
      [s["name"] for s in r["stores"]] == ["Amazon.co.uk", "eBay.co.uk", "Facebook Marketplace"]
      and r["currency"] == "GBP" and r["fb_city"] == "london")
check("an unknown country is refused", client.get("/api/stores?region=ZZ").status_code == 400)
r = client.get("/api/stores?region=US")
check("asking for the US points to the other edition", r.status_code == 400 and "US-CANADA" in r.get_json()["error"])
for it in st5.items:
    sc5._due[(it["id"], "amazon")] = time.time() + 900
client.patch("/api/settings", json={"speed": "fast"})
check("an ordinary settings change leaves the stores' clocks alone",
      all(v > time.time() for (i, k), v in sc5._due.items() if k == "amazon" and not i.startswith("i")))
client.patch("/api/settings", json={"region": "DE"})
check("moving to another country makes every store due at once, instead of after the old country's clocks",
      all(v == 0.0 for (i, k), v in sc5._due.items() if k == "amazon" and not i.startswith("i")))

for p in paths:
    for f in (p, p + ".tmp", p + ".bak"):
        if os.path.exists(f):
            os.remove(f)
for f in os.listdir(tempfile.gettempdir()):
    if f.startswith("ihtest_") and ".corrupt-" in f:
        os.remove(os.path.join(tempfile.gettempdir(), f))
print("\nALL PASS" if ok else "\nSOME FAILED")
sys.exit(0 if ok else 1)
