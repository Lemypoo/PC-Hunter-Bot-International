import re
import threading
import time
from urllib.parse import quote_plus

from .. import countries
from ..money import detect_currency, parse_last_money
from .base import Listing, Source, SourceError, parse_money, site_label

# One search-result card -> the new-in-box price, plus the "£X (N used & new offers)" line that
# Amazon prints under a result when other sellers (used, open box, third party) undercut it.
# Pages are requested in English where the marketplace has it; the other languages are here for
# the marketplaces that ignore the request.
JS = r"""() => [...document.querySelectorAll('div[data-component-type="s-search-result"]')].map(c => {
  const h2 = c.querySelector('h2');
  const a = c.querySelector('a.a-link-normal.s-no-outline') || c.querySelector('h2 a') || c.querySelector('a[href*="/dp/"]');
  const box = c.querySelector('.a-price[data-a-color="base"]') || c.querySelector('.a-price:not([data-a-strike])') || c.querySelector('.a-price');
  const off = box ? box.querySelector('.a-offscreen') : null;
  const whole = box ? box.querySelector('.a-price-whole') : null;
  const frac = box ? box.querySelector('.a-price-fraction') : null;
  const was = c.querySelector('.a-price[data-a-strike="true"] .a-offscreen') || c.querySelector('.a-text-price .a-offscreen');
  const txt = c.innerText || '';
  const ttl = h2 ? h2.innerText.trim() : '';
  const mo = txt.match(/([^\n(]{0,40})\(\s*(\d+)\+?\s+(used & new|used|new)\s+offers?\s*\)/i);
  return {
    id: c.dataset.asin || '',
    title: ttl,
    url: a ? a.href : '',
    price: off ? off.textContent : '',
    whole: whole ? whole.textContent : '',
    frac: frac ? frac.textContent : '',
    was: was ? was.textContent : '',
    offers: mo ? {text: mo[1], count: mo[2], kind: mo[3].toLowerCase()} : null,
    sponsored: /\b(Sponsored|Gesponsert|Sponsorisé|Sponsorizzato|Patrocinado|Gesponsord|Sponsrad|Sponsorowane|Sponsorlu)\b|スポンサー/.test(txt),
    unavailable: /Currently unavailable|Temporarily out of stock|Derzeit nicht verfügbar|Vorübergehend nicht auf Lager|Actuellement indisponible|Temporairement en rupture|Attualmente non disponibile|Temporaneamente non disponibile|No disponible por el momento|Temporalmente sin stock|Momenteel niet verkrijgbaar|Tijdelijk niet op voorraad|För närvarande inte tillgänglig|Tillfälligt slut|Obecnie niedostępny|Chwilowo niedostępny|Şu anda mevcut değil|Não disponível|Temporariamente fora de estoque|現在在庫切れです|一時的に在庫切れ/i.test(txt),
    used: /\b(Used|Renewed|Refurbished|Gebraucht|Generalüberholt|Reconditionné|Ricondizionato|Reacondicionado|Gereviseerd|Renoverad|Odnowiony|Yenilenmiş|Recondicionado)\b|整備済み|中古/i.test(ttl),
  };
})"""
RESULTS = 'div[data-component-type="s-search-result"], :text("No results for"), form[action*="validateCaptcha"]'

# What kind of page did Amazon actually hand back? A robot check has the same "Amazon.xx" title as a
# real page, so the title alone cannot tell them apart.
PAGE_STATE_JS = r"""() => ({
  cards: document.querySelectorAll('div[data-component-type="s-search-result"]').length,
  captcha: !!document.querySelector('form[action*="validateCaptcha"], #captchacharacters'),
  noResults: /No results for|did not match any products|Keine Ergebnisse für|Aucun résultat pour|Nessun risultato per|No hay resultados para|Geen resultaten voor|Inga resultat för|Brak wyników dla|için sonuç bulunamadı|Nenhum resultado para|に一致する商品はありませんでした/i.test(document.body ? document.body.innerText : ''),
})"""
SPONSORED_PREFIX = re.compile(r"^\s*(Sponsored Ad|Gesponserte Anzeige|Annonce sponsorisée|Annuncio sponsorizzato|"
                              r"Anuncio patrocinado)\s*[-–]\s*", re.I)

# The Resale page changes slowly, and fetching it every check doubled Amazon traffic. Reuse it for a while.
RESALE_REFRESH = 20 * 60
_resale_cache = {}            # (site, query) -> (fetched_at, raw rows)
_resale_lock = threading.Lock()


def card_price(r, cur):
    """A result card's (price, currency). The whole and fraction parts are separate elements on every
    marketplace, so reading them avoids guessing whether "1.299" is a thousand or one and a bit. The
    currency is read off the card: Amazon.com shows visitors from abroad their own currency
    ("CAD 16,358.58"), so the marketplace's currency is only the fallback."""
    shown = detect_currency(r.get("price") or "", cur)
    whole = re.sub(r"\D", "", r.get("whole") or "")
    if whole:
        frac = re.sub(r"\D", "", r.get("frac") or "")
        value = float(f"{whole}.{frac}") if frac else float(whole)
        return (value if value > 0 else None), shown
    return parse_money(r.get("price"), cur)[0], shown


class Amazon(Source):
    key = "amazon"
    name = "Amazon"
    min_gap = 20
    interval = 900    # Amazon throttles a home connection that searches it often; keep it slow

    @classmethod
    def supports(cls, region):
        return countries.amazon_site(region) is not None

    @staticmethod
    def site(region):
        return countries.amazon_site(region)

    def display_name(self, region):
        return site_label(self.site(region) or "amazon.com")

    def note(self, region):
        site = self.site(region)
        if not site or region in countries.AMAZON_OWN:
            return ""
        text = f"no Amazon store in {countries.name(region)}; check that an item ships to you"
        if not (countries.area(region) == "EU" and site in countries.EU_AMAZON):
            text += ", import fees not included"   # none inside the EU single market
        return text

    def site_currency(self, region):
        return countries.AMAZON_SITES[self.site(region)][0]

    @staticmethod
    def _clean(r):
        asin = (r.get("id") or "").strip()
        title = SPONSORED_PREFIX.sub("", r.get("title") or "").strip()
        return asin, title

    def _load(self, page, url):
        """Open an Amazon search page and make sure it really is one. Returns the result cards."""
        self.goto(page, url, wait_for=RESULTS)
        state = page.evaluate(PAGE_STATE_JS)
        if state.get("captcha"):
            raise SourceError("blocked (Amazon is showing a robot check)")
        if not state.get("cards"):
            if state.get("noResults"):
                return []
            raise SourceError("Amazon returned a page with no search results (throttled or still loading)")
        return page.evaluate(JS)

    def search(self, page, query, region):
        site = self.site(region)
        if not site:
            raise SourceError(f"Amazon does not sell to {countries.name(region)}")
        cur, lang, has_resale = countries.AMAZON_SITES[site]
        base = f"https://www.{site}"
        name = site_label(site)
        want_used = self.settings.get("include_used", True)
        new = {}    # asin -> Listing; the same product can appear twice (sponsored and organic)
        used = {}   # asin -> the one cheapest non-new offer, so an ASIN gets a single used row

        def note_used(asin, title, price, currency, condition, seller):
            best = used.get(asin)
            if best is not None and best.currency != currency:
                return    # two currencies for one product's offers: keep the first rather than compare
            if best is None or price < best.price:
                used[asin] = Listing(
                    source=self.key, source_name=name, id=f"{asin}:used", title=title,
                    url=f"{base}/gp/offer-listing/{asin}?condition=used", price=price, currency=currency,
                    in_stock=True, condition=condition, seller=seller, region=region,
                )
            elif price == best.price and seller == "Amazon Resale":
                best.condition, best.seller = condition, seller   # the more specific label wins

        # 1. the regular search: new-in-box price, plus the cheapest "used & new" offer per result
        for r in self._load(page, f"{base}/s?k={quote_plus(query)}&language={lang}"):
            asin, title = self._clean(r)
            if not asin or not title:
                continue
            price, shown = card_price(r, cur)
            if price is not None and (asin not in new or price < new[asin].price):
                new[asin] = Listing(
                    source=self.key, source_name=name, id=asin, title=title, url=f"{base}/dp/{asin}",
                    price=price, currency=shown, in_stock=not r.get("unavailable"),
                    condition="Used" if r.get("used") else "New",
                    was_price=parse_money(r.get("was"), shown)[0], sponsored=bool(r.get("sponsored")),
                    region=region,
                )
            off = r.get("offers")
            if want_used and off and "used" in off.get("kind", ""):
                other, ocur = parse_last_money(off.get("text"), shown)
                if other is not None and (price is None or (ocur == shown and other < price)):
                    note_used(asin, title, other, ocur, f"Used or new, cheapest of {off['count']} offers",
                              "Other sellers")

        # 2. Amazon Resale (the old Warehouse Deals): open-box and used stock sold by Amazon itself.
        # Only where the storefront exists; elsewhere the search would quietly return new stock.
        if want_used and has_resale:
            for r in self._resale_rows(page, base, lang, query):
                asin, title = self._clean(r)
                if not asin or not title:
                    continue
                off = r.get("offers")
                price, shown = card_price(r, cur)
                if price is None and off:
                    price, shown = parse_last_money(off.get("text"), cur)
                if price is None:
                    continue
                count = int(off["count"]) if off and str(off.get("count", "")).isdigit() else 1
                note_used(asin, title, price, shown,
                          "Used, Amazon Resale" + (f", {count} offers" if count > 1 else ""),
                          "Amazon Resale")
        return list(new.values()) + list(used.values())

    def _resale_rows(self, page, base, lang, query):
        """Resale results, fetched at most every RESALE_REFRESH seconds per query."""
        key = (base, query.strip().lower())
        with _resale_lock:
            cached = _resale_cache.get(key)
        if cached and time.time() - cached[0] < RESALE_REFRESH:
            return cached[1]
        page.wait_for_timeout(2500)
        try:
            rows = self._load(page, f"{base}/s?k={quote_plus(query)}&i=warehouse-deals&language={lang}")
        except SourceError as e:
            if "blocked" in str(e).lower():
                raise                      # a robot check means Amazon wants us gone; back off
            return cached[1] if cached else []   # a flaky Resale page should not sink the main search
        with _resale_lock:
            _resale_cache[key] = (time.time(), rows)
        return rows
