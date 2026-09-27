from .amazon import Amazon
from .ebay import Ebay
from .facebook import Facebook, city_slug

ALL = [Amazon, Ebay, Facebook]
REGISTRY = {s.key: s for s in ALL}
RETAIL_KEYS = {s.key for s in ALL if s.retail}   # real shops: their prices anchor the placeholder floor


def describe(settings=None, region=None):
    """The stores that serve a country, as the Settings dialog lists them."""
    settings = settings or {}
    region = region or settings.get("region", "GB")
    out = []
    for S in ALL:
        if not S.supports(region):
            continue
        s = S(settings)
        out.append({"key": S.key, "name": s.display_name(region), "note": s.note(region)})
    return out


def sources_for(settings):
    """Stores to check right now: serving this country, switched on, and ready (Facebook needs a city)."""
    region = settings.get("region", "GB")
    enabled = settings.get("sources") or {}
    out = []
    for S in ALL:
        if not S.supports(region) or not enabled.get(S.key, True):
            continue
        if S is Facebook and not city_slug(settings.get("fb_city")):
            continue
        out.append(S(settings))
    return out


def active_keys(settings, item=None) -> set:
    """Store keys that count for an item right now: switched on, in this country, and on the
    item's own list if it has one. Listings from any other store are kept but not shown."""
    keys = {s.key for s in sources_for(settings)}
    if item and item.get("sources"):
        keys &= set(item["sources"])
    return keys


def is_used_offer(rec) -> bool:
    """A row that stands for the used and open-box offers on a product rather than new stock."""
    return str(rec.get("id") or "").endswith(":used")


def counts_now(settings, rec, keys) -> bool:
    """Should this stored listing show on the card and count towards the best price?
    Listings found under another country setting stay stored but out of sight."""
    if rec.get("source") not in keys:
        return False
    if rec.get("region") and rec["region"] != settings.get("region"):
        return False
    return settings.get("include_used", True) or not is_used_offer(rec)
