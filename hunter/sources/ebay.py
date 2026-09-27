import re
from urllib.parse import quote_plus

from .. import countries
from .base import Listing, Source, SourceError, parse_money, site_label

# "For parts or not working" in every language eBay's sites use; not a purchase option for a build.
PARTS_RE = re.compile(
    r"parts only|for parts|not working|defective|broken|faulty|"
    r"ersatzteil|defekt|pour pièces|pièces détachées|ne fonctionne pas|hors service|"
    r"per parti di ricambio|solo ricambi|non funzionante|guasto|para piezas|no funciona|averiado|"
    r"voor onderdelen|werkt niet|kapot|na części|uszkodzon|niesprawn", re.I)
# The "from <country>" line under a result, in the site's language.
FROM_RE = re.compile(r"^(?:from|aus|de|en provenance de|da|desde|uit|z|z kraju)\s+(.+)$", re.I)
SHIP_RE = re.compile(r"shipping|delivery|postage|pickup|lieferung|versand|livraison|spedizione|envío|envio|"
                     r"verzending|wysyłka|dostawa|abholung|retrait|ritiro|recogida|ophalen|odbiór", re.I)

JS = r"""() => [...document.querySelectorAll('li.s-card[data-listingid], li.s-item')].map(c => {
  const a = c.querySelector('a.s-card__link, a.s-item__link') || c.querySelector('a[href*="/itm/"]');
  const t = c.querySelector('.s-card__title, .s-item__title');
  const p = c.querySelector('.s-card__price, .s-item__price');
  const sub = c.querySelector('.s-card__subtitle, .SECONDARY_INFO');
  const rows = [...c.querySelectorAll('.s-card__attribute-row, .s-item__detail')].map(r => r.innerText.trim()).filter(Boolean);
  return {
    id: c.dataset.listingid || '',
    title: t ? t.innerText.replace(/Opens in a new window or tab|Wird in neuem Fenster oder Tab geöffnet|S'ouvre dans une nouvelle fenêtre ou un nouvel onglet|Si apre in una nuova finestra o scheda|Se abre en una nueva ventana o pestaña|Wordt geopend in een nieuw venster of tabblad|Otwiera się w nowym oknie lub karcie/g, '').replace(/^(New Listing|Neues Angebot|Nouvelle annonce|Nuova inserzione|Nuevo anuncio|Nieuwe advertentie|Nowa oferta)/i, '').trim() : '',
    url: a ? a.href : '',
    price: p ? p.innerText : '',
    condition: sub ? sub.innerText.trim() : '',
    rows,
  };
})"""
PLACEHOLDER_TITLES = {"shop on ebay", "bei ebay einkaufen", "achetez sur ebay", "acquista su ebay",
                      "compra en ebay", "winkel op ebay", "kupuj na ebay"}


class Ebay(Source):
    key = "ebay"
    name = "eBay"
    retail = False
    min_gap = 20      # serves an error page after bursts
    interval = 240

    @classmethod
    def supports(cls, region):
        return countries.ebay_site(region) is not None

    @staticmethod
    def site(region):
        return countries.ebay_site(region)

    def display_name(self, region):
        return site_label(self.site(region) or "www.ebay.com")

    def note(self, region):
        site = self.site(region)
        if site and region not in countries.EBAY_OWN:
            return f"no eBay site for {countries.name(region)}; check that an item ships to you"
        return ""

    def search(self, page, query, region):
        host = self.site(region)
        if not host:
            raise SourceError(f"eBay does not sell to {countries.name(region)}")
        cur = countries.EBAY_SITES[host]
        name = site_label(host)
        # _sop=15: price + shipping, lowest first. LH_BIN=1: Buy It Now only (auction bids mislead).
        url = f"https://{host}/sch/i.html?_nkw={quote_plus(query)}&_sop=15&LH_BIN=1"
        self.goto(page, url, wait_for="li.s-card, li.s-item")
        rows = page.evaluate(JS)
        out = []
        for r in rows:
            link = r.get("url") or ""
            m = re.search(r"/itm/(\d{6,})", link)
            item_id = r.get("id") or (m.group(1) if m else "")
            title = (r.get("title") or "").strip()
            if not item_id or item_id == "123456" or "/itm/123456" in link or title.lower() in PLACEHOLDER_TITLES:
                continue  # eBay's placeholder cards
            price, pcur = parse_money(r.get("price"), cur)
            if not title or price is None:
                continue
            if PARTS_RE.search(r.get("condition") or ""):
                continue
            ship, loc = "", ""
            for row in r.get("rows") or []:
                if not ship and SHIP_RE.search(row):
                    ship = row
                fm = FROM_RE.match(row)
                if not loc and fm and len(fm.group(1)) <= 40 and not SHIP_RE.search(row) \
                        and not re.search(r"\d", row):   # "de 10 € de livraison" is postage, not a place
                    loc = fm.group(1).strip()
            out.append(Listing(
                source=self.key, source_name=name, id=item_id, title=title,
                url=f"https://{host}/itm/{item_id}", price=price, currency=pcur or cur,
                in_stock=True, condition=r.get("condition") or "", location=loc, seller=ship, region=region,
            ))
        return out
