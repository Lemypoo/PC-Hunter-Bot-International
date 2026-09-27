"""Every country the app can be set to: its name, its currency, and which Amazon and eBay site serves it.

Canada and the United States are left to the Canada and US edition of Item Hunter
(github.com/Lemypoo/PC-Hunter-Bot-US-CANADA), which also covers their national retailers. They stay in the table
below only so that data brought over from that edition can still be read.

A country with its own Amazon or eBay site gets that site. A country without one gets the nearest site
that sells to it (Austria gets Amazon.de, New Zealand gets Amazon.com.au, most others Amazon.com), and
prices from there are converted into the country's currency for comparison.
"""

# code: (name, currency, area). Areas only decide the fallback store sites below.
COUNTRIES = {
    "AF": ("Afghanistan", "AFN", "ASIA"),
    "AX": ("Åland Islands", "EUR", "EU"),
    "AL": ("Albania", "ALL", "EUROPE"),
    "DZ": ("Algeria", "DZD", "MENA"),
    "AS": ("American Samoa", "USD", "USTERR"),
    "AD": ("Andorra", "EUR", "EUROPE"),
    "AO": ("Angola", "AOA", "AFRICA"),
    "AI": ("Anguilla", "XCD", "LATAM"),
    "AG": ("Antigua and Barbuda", "XCD", "LATAM"),
    "AR": ("Argentina", "ARS", "LATAM"),
    "AM": ("Armenia", "AMD", "ASIA"),
    "AW": ("Aruba", "AWG", "LATAM"),
    "AU": ("Australia", "AUD", "OCEANIA"),
    "AT": ("Austria", "EUR", "EU"),
    "AZ": ("Azerbaijan", "AZN", "ASIA"),
    "BS": ("Bahamas", "BSD", "LATAM"),
    "BH": ("Bahrain", "BHD", "GULF"),
    "BD": ("Bangladesh", "BDT", "ASIA"),
    "BB": ("Barbados", "BBD", "LATAM"),
    "BY": ("Belarus", "BYN", "EUROPE"),
    "BE": ("Belgium", "EUR", "EU"),
    "BZ": ("Belize", "BZD", "LATAM"),
    "BJ": ("Benin", "XOF", "AFRICA"),
    "BM": ("Bermuda", "BMD", "LATAM"),
    "BT": ("Bhutan", "BTN", "ASIA"),
    "BO": ("Bolivia", "BOB", "LATAM"),
    "BQ": ("Caribbean Netherlands", "USD", "LATAM"),
    "BA": ("Bosnia and Herzegovina", "BAM", "EUROPE"),
    "BW": ("Botswana", "BWP", "AFRICA"),
    "BR": ("Brazil", "BRL", "LATAM"),
    "VG": ("British Virgin Islands", "USD", "LATAM"),
    "BN": ("Brunei", "BND", "ASIA"),
    "BG": ("Bulgaria", "EUR", "EU"),
    "BF": ("Burkina Faso", "XOF", "AFRICA"),
    "BI": ("Burundi", "BIF", "AFRICA"),
    "CV": ("Cabo Verde", "CVE", "AFRICA"),
    "KH": ("Cambodia", "KHR", "ASIA"),
    "CM": ("Cameroon", "XAF", "AFRICA"),
    "CA": ("Canada", "CAD", "NA"),
    "KY": ("Cayman Islands", "KYD", "LATAM"),
    "CF": ("Central African Republic", "XAF", "AFRICA"),
    "TD": ("Chad", "XAF", "AFRICA"),
    "CL": ("Chile", "CLP", "LATAM"),
    "CN": ("China", "CNY", "ASIA"),
    "CX": ("Christmas Island", "AUD", "AUTERR"),
    "CC": ("Cocos (Keeling) Islands", "AUD", "AUTERR"),
    "CO": ("Colombia", "COP", "LATAM"),
    "KM": ("Comoros", "KMF", "AFRICA"),
    "CG": ("Congo", "XAF", "AFRICA"),
    "CD": ("Congo (DRC)", "CDF", "AFRICA"),
    "CK": ("Cook Islands", "NZD", "OCEANIA"),
    "CR": ("Costa Rica", "CRC", "LATAM"),
    "CI": ("Côte d'Ivoire", "XOF", "AFRICA"),
    "HR": ("Croatia", "EUR", "EU"),
    "CU": ("Cuba", "CUP", "LATAM"),
    "CW": ("Curaçao", "XCG", "LATAM"),
    "CY": ("Cyprus", "EUR", "EU"),
    "CZ": ("Czechia", "CZK", "EU"),
    "DK": ("Denmark", "DKK", "EU"),
    "DJ": ("Djibouti", "DJF", "AFRICA"),
    "DM": ("Dominica", "XCD", "LATAM"),
    "DO": ("Dominican Republic", "DOP", "LATAM"),
    "EC": ("Ecuador", "USD", "LATAM"),
    "EG": ("Egypt", "EGP", "MENA"),
    "SV": ("El Salvador", "USD", "LATAM"),
    "GQ": ("Equatorial Guinea", "XAF", "AFRICA"),
    "ER": ("Eritrea", "ERN", "AFRICA"),
    "EE": ("Estonia", "EUR", "EU"),
    "SZ": ("Eswatini", "SZL", "AFRICA"),
    "ET": ("Ethiopia", "ETB", "AFRICA"),
    "FK": ("Falkland Islands", "FKP", "UKTERR"),
    "FO": ("Faroe Islands", "DKK", "EUROPE"),
    "FJ": ("Fiji", "FJD", "OCEANIA"),
    "FI": ("Finland", "EUR", "EU"),
    "FR": ("France", "EUR", "EU"),
    "GF": ("French Guiana", "EUR", "FRTERR"),
    "PF": ("French Polynesia", "XPF", "FRTERR"),
    "GA": ("Gabon", "XAF", "AFRICA"),
    "GM": ("Gambia", "GMD", "AFRICA"),
    "GE": ("Georgia", "GEL", "EUROPE"),
    "DE": ("Germany", "EUR", "EU"),
    "GH": ("Ghana", "GHS", "AFRICA"),
    "GI": ("Gibraltar", "GIP", "UKTERR"),
    "GR": ("Greece", "EUR", "EU"),
    "GL": ("Greenland", "DKK", "EUROPE"),
    "GD": ("Grenada", "XCD", "LATAM"),
    "GP": ("Guadeloupe", "EUR", "FRTERR"),
    "GU": ("Guam", "USD", "USTERR"),
    "GT": ("Guatemala", "GTQ", "LATAM"),
    "GG": ("Guernsey", "GBP", "UKTERR"),
    "GN": ("Guinea", "GNF", "AFRICA"),
    "GW": ("Guinea-Bissau", "XOF", "AFRICA"),
    "GY": ("Guyana", "GYD", "LATAM"),
    "HT": ("Haiti", "HTG", "LATAM"),
    "HN": ("Honduras", "HNL", "LATAM"),
    "HK": ("Hong Kong", "HKD", "ASIA"),
    "HU": ("Hungary", "HUF", "EU"),
    "IS": ("Iceland", "ISK", "EUROPE"),
    "IN": ("India", "INR", "ASIA"),
    "ID": ("Indonesia", "IDR", "ASIA"),
    "IR": ("Iran", "IRR", "MENA"),
    "IQ": ("Iraq", "IQD", "MENA"),
    "IE": ("Ireland", "EUR", "EU"),
    "IM": ("Isle of Man", "GBP", "UKTERR"),
    "IL": ("Israel", "ILS", "MENA"),
    "IT": ("Italy", "EUR", "EU"),
    "JM": ("Jamaica", "JMD", "LATAM"),
    "JP": ("Japan", "JPY", "ASIA"),
    "JE": ("Jersey", "GBP", "UKTERR"),
    "JO": ("Jordan", "JOD", "MENA"),
    "KZ": ("Kazakhstan", "KZT", "ASIA"),
    "KE": ("Kenya", "KES", "AFRICA"),
    "KI": ("Kiribati", "AUD", "OCEANIA"),
    "XK": ("Kosovo", "EUR", "EUROPE"),
    "KW": ("Kuwait", "KWD", "GULF"),
    "KG": ("Kyrgyzstan", "KGS", "ASIA"),
    "LA": ("Laos", "LAK", "ASIA"),
    "LV": ("Latvia", "EUR", "EU"),
    "LB": ("Lebanon", "LBP", "MENA"),
    "LS": ("Lesotho", "LSL", "AFRICA"),
    "LR": ("Liberia", "LRD", "AFRICA"),
    "LY": ("Libya", "LYD", "MENA"),
    "LI": ("Liechtenstein", "CHF", "EUROPE"),
    "LT": ("Lithuania", "EUR", "EU"),
    "LU": ("Luxembourg", "EUR", "EU"),
    "MO": ("Macao", "MOP", "ASIA"),
    "MG": ("Madagascar", "MGA", "AFRICA"),
    "MW": ("Malawi", "MWK", "AFRICA"),
    "MY": ("Malaysia", "MYR", "ASIA"),
    "MV": ("Maldives", "MVR", "ASIA"),
    "ML": ("Mali", "XOF", "AFRICA"),
    "MT": ("Malta", "EUR", "EU"),
    "MH": ("Marshall Islands", "USD", "OCEANIA"),
    "MQ": ("Martinique", "EUR", "FRTERR"),
    "MR": ("Mauritania", "MRU", "AFRICA"),
    "MU": ("Mauritius", "MUR", "AFRICA"),
    "YT": ("Mayotte", "EUR", "FRTERR"),
    "MX": ("Mexico", "MXN", "LATAM"),
    "FM": ("Micronesia", "USD", "OCEANIA"),
    "MD": ("Moldova", "MDL", "EUROPE"),
    "MC": ("Monaco", "EUR", "EUROPE"),
    "MN": ("Mongolia", "MNT", "ASIA"),
    "ME": ("Montenegro", "EUR", "EUROPE"),
    "MS": ("Montserrat", "XCD", "LATAM"),
    "MA": ("Morocco", "MAD", "MENA"),
    "MZ": ("Mozambique", "MZN", "AFRICA"),
    "MM": ("Myanmar", "MMK", "ASIA"),
    "NA": ("Namibia", "NAD", "AFRICA"),
    "NR": ("Nauru", "AUD", "OCEANIA"),
    "NP": ("Nepal", "NPR", "ASIA"),
    "NL": ("Netherlands", "EUR", "EU"),
    "NC": ("New Caledonia", "XPF", "FRTERR"),
    "NZ": ("New Zealand", "NZD", "OCEANIA"),
    "NI": ("Nicaragua", "NIO", "LATAM"),
    "NE": ("Niger", "XOF", "AFRICA"),
    "NG": ("Nigeria", "NGN", "AFRICA"),
    "NU": ("Niue", "NZD", "OCEANIA"),
    "NF": ("Norfolk Island", "AUD", "AUTERR"),
    "KP": ("North Korea", "KPW", "ASIA"),
    "MK": ("North Macedonia", "MKD", "EUROPE"),
    "MP": ("Northern Mariana Islands", "USD", "USTERR"),
    "NO": ("Norway", "NOK", "EUROPE"),
    "OM": ("Oman", "OMR", "GULF"),
    "PK": ("Pakistan", "PKR", "ASIA"),
    "PW": ("Palau", "USD", "OCEANIA"),
    "PS": ("Palestine", "ILS", "MENA"),
    "PA": ("Panama", "USD", "LATAM"),     # the balboa is pegged 1:1 and prices are quoted in US dollars
    "PG": ("Papua New Guinea", "PGK", "OCEANIA"),
    "PY": ("Paraguay", "PYG", "LATAM"),
    "PE": ("Peru", "PEN", "LATAM"),
    "PH": ("Philippines", "PHP", "ASIA"),
    "PL": ("Poland", "PLN", "EU"),
    "PT": ("Portugal", "EUR", "EU"),
    "PR": ("Puerto Rico", "USD", "USTERR"),
    "QA": ("Qatar", "QAR", "GULF"),
    "RE": ("Réunion", "EUR", "FRTERR"),
    "RO": ("Romania", "RON", "EU"),
    "RU": ("Russia", "RUB", "EUROPE"),
    "RW": ("Rwanda", "RWF", "AFRICA"),
    "BL": ("Saint Barthélemy", "EUR", "FRTERR"),
    "SH": ("Saint Helena", "SHP", "UKTERR"),
    "KN": ("Saint Kitts and Nevis", "XCD", "LATAM"),
    "LC": ("Saint Lucia", "XCD", "LATAM"),
    "MF": ("Saint Martin", "EUR", "FRTERR"),
    "PM": ("Saint Pierre and Miquelon", "EUR", "FRTERR"),
    "VC": ("Saint Vincent and the Grenadines", "XCD", "LATAM"),
    "WS": ("Samoa", "WST", "OCEANIA"),
    "SM": ("San Marino", "EUR", "EUROPE"),
    "ST": ("São Tomé and Príncipe", "STN", "AFRICA"),
    "SA": ("Saudi Arabia", "SAR", "GULF"),
    "SN": ("Senegal", "XOF", "AFRICA"),
    "RS": ("Serbia", "RSD", "EUROPE"),
    "SC": ("Seychelles", "SCR", "AFRICA"),
    "SL": ("Sierra Leone", "SLE", "AFRICA"),
    "SG": ("Singapore", "SGD", "ASIA"),
    "SX": ("Sint Maarten", "XCG", "LATAM"),
    "SK": ("Slovakia", "EUR", "EU"),
    "SI": ("Slovenia", "EUR", "EU"),
    "SB": ("Solomon Islands", "SBD", "OCEANIA"),
    "SO": ("Somalia", "SOS", "AFRICA"),
    "ZA": ("South Africa", "ZAR", "AFRICA"),
    "KR": ("South Korea", "KRW", "ASIA"),
    "SS": ("South Sudan", "SSP", "AFRICA"),
    "ES": ("Spain", "EUR", "EU"),
    "LK": ("Sri Lanka", "LKR", "ASIA"),
    "SD": ("Sudan", "SDG", "AFRICA"),
    "SR": ("Suriname", "SRD", "LATAM"),
    "SE": ("Sweden", "SEK", "EU"),
    "CH": ("Switzerland", "CHF", "EUROPE"),
    "SY": ("Syria", "SYP", "MENA"),
    "TW": ("Taiwan", "TWD", "ASIA"),
    "TJ": ("Tajikistan", "TJS", "ASIA"),
    "TZ": ("Tanzania", "TZS", "AFRICA"),
    "TH": ("Thailand", "THB", "ASIA"),
    "TL": ("Timor-Leste", "USD", "ASIA"),
    "TG": ("Togo", "XOF", "AFRICA"),
    "TK": ("Tokelau", "NZD", "OCEANIA"),
    "TO": ("Tonga", "TOP", "OCEANIA"),
    "TT": ("Trinidad and Tobago", "TTD", "LATAM"),
    "TN": ("Tunisia", "TND", "MENA"),
    "TR": ("Türkiye", "TRY", "EUROPE"),
    "TM": ("Turkmenistan", "TMT", "ASIA"),
    "TC": ("Turks and Caicos Islands", "USD", "LATAM"),
    "TV": ("Tuvalu", "AUD", "OCEANIA"),
    "VI": ("U.S. Virgin Islands", "USD", "USTERR"),
    "UG": ("Uganda", "UGX", "AFRICA"),
    "UA": ("Ukraine", "UAH", "EUROPE"),
    "AE": ("United Arab Emirates", "AED", "GULF"),
    "GB": ("United Kingdom", "GBP", "EUROPE"),
    "US": ("United States", "USD", "NA"),
    "UY": ("Uruguay", "UYU", "LATAM"),
    "UZ": ("Uzbekistan", "UZS", "ASIA"),
    "VU": ("Vanuatu", "VUV", "OCEANIA"),
    "VA": ("Vatican City", "EUR", "EUROPE"),
    "VE": ("Venezuela", "VES", "LATAM"),
    "VN": ("Vietnam", "VND", "ASIA"),
    "WF": ("Wallis and Futuna", "XPF", "FRTERR"),
    "YE": ("Yemen", "YER", "MENA"),
    "ZM": ("Zambia", "ZMW", "AFRICA"),
    "ZW": ("Zimbabwe", "USD", "AFRICA"),   # the ZiG is official, but shops and listings price in US dollars
}

# The Canada and US edition covers these two, with their own retailers.
OTHER_EDITION = {"CA", "US"}
OTHER_EDITION_URL = "https://github.com/Lemypoo/PC-Hunter-Bot-US-CANADA"
DEFAULT_COUNTRY = "GB"       # first start on a computer set to Canada or the US, or to no country at all

# Amazon and eBay do not sell to these (sanctions), so neither is offered there.
EMBARGOED = {"CU", "IR", "KP", "RU", "BY", "SY"}

# ---------- Amazon ----------
# domain: (currency, language to ask for, has the Resale / Warehouse storefront)
# The language parameter turns most non-English marketplaces into English pages, which is what the
# page reader understands best. A marketplace that has no English simply ignores it.
AMAZON_SITES = {
    "amazon.com": ("USD", "en_US", True),     # for countries with no nearer marketplace
    "amazon.com.mx": ("MXN", "en_US", False),
    "amazon.com.br": ("BRL", "en_US", False),
    "amazon.co.uk": ("GBP", "en_GB", True),
    "amazon.ie": ("EUR", "en_GB", False),
    "amazon.de": ("EUR", "en_GB", True),
    "amazon.fr": ("EUR", "en_GB", True),
    "amazon.it": ("EUR", "en_GB", True),
    "amazon.es": ("EUR", "en_GB", True),
    "amazon.nl": ("EUR", "en_GB", False),
    "amazon.com.be": ("EUR", "en_GB", False),
    "amazon.se": ("SEK", "en_GB", False),
    "amazon.pl": ("PLN", "en_GB", False),
    "amazon.com.tr": ("TRY", "en_US", False),
    "amazon.ae": ("AED", "en_AE", False),
    "amazon.sa": ("SAR", "en_AE", False),
    "amazon.eg": ("EGP", "en_AE", False),
    "amazon.in": ("INR", "en_IN", False),
    "amazon.co.jp": ("JPY", "en_US", False),
    "amazon.com.au": ("AUD", "en_AU", False),
    "amazon.sg": ("SGD", "en_SG", False),
    "amazon.co.za": ("ZAR", "en_ZA", False),
}
AMAZON_OWN = {
    "MX": "amazon.com.mx", "BR": "amazon.com.br",
    "GB": "amazon.co.uk", "IE": "amazon.ie", "DE": "amazon.de", "FR": "amazon.fr", "IT": "amazon.it",
    "ES": "amazon.es", "NL": "amazon.nl", "BE": "amazon.com.be", "SE": "amazon.se", "PL": "amazon.pl",
    "TR": "amazon.com.tr", "AE": "amazon.ae", "SA": "amazon.sa", "EG": "amazon.eg", "IN": "amazon.in",
    "JP": "amazon.co.jp", "AU": "amazon.com.au", "SG": "amazon.sg", "ZA": "amazon.co.za",
}
# Countries without their own marketplace that a neighbour serves better than Amazon.com does.
AMAZON_NEAR = {
    "PT": "amazon.es", "AD": "amazon.es", "MC": "amazon.fr", "SM": "amazon.it", "VA": "amazon.it",
    "NZ": "amazon.com.au", "FJ": "amazon.com.au", "LU": "amazon.de", "LI": "amazon.de", "CH": "amazon.de",
}
EU_AMAZON = {"amazon.de", "amazon.fr", "amazon.it", "amazon.es", "amazon.nl", "amazon.com.be", "amazon.se",
             "amazon.pl", "amazon.ie"}
AMAZON_BY_AREA = {
    "EU": "amazon.de", "EUROPE": "amazon.de", "UKTERR": "amazon.co.uk", "FRTERR": "amazon.fr",
    "AUTERR": "amazon.com.au", "GULF": "amazon.ae", "USTERR": "amazon.com",
}

# ---------- eBay ----------
EBAY_SITES = {   # host: currency
    "www.ebay.com": "USD", "www.ebay.co.uk": "GBP", "www.ebay.de": "EUR",
    "www.ebay.fr": "EUR", "www.ebay.it": "EUR", "www.ebay.es": "EUR", "www.ebay.com.au": "AUD",
    "www.ebay.at": "EUR", "www.ebay.ch": "CHF", "www.ebay.ie": "EUR", "www.befr.ebay.be": "EUR",
    "www.ebay.nl": "EUR", "www.ebay.pl": "PLN", "www.ebay.com.hk": "HKD", "www.ebay.com.sg": "SGD",
    "www.ebay.com.my": "MYR", "www.ebay.ph": "PHP",
}
EBAY_OWN = {
    "GB": "www.ebay.co.uk", "DE": "www.ebay.de",
    "FR": "www.ebay.fr", "IT": "www.ebay.it", "ES": "www.ebay.es", "AU": "www.ebay.com.au",
    "AT": "www.ebay.at", "CH": "www.ebay.ch", "IE": "www.ebay.ie", "BE": "www.befr.ebay.be",
    "NL": "www.ebay.nl", "PL": "www.ebay.pl", "HK": "www.ebay.com.hk", "SG": "www.ebay.com.sg",
    "MY": "www.ebay.com.my", "PH": "www.ebay.ph",
}
EBAY_NEAR = {
    "PT": "www.ebay.es", "AD": "www.ebay.es", "MC": "www.ebay.fr", "SM": "www.ebay.it",
    "VA": "www.ebay.it", "LI": "www.ebay.ch", "NZ": "www.ebay.com.au", "LU": "www.ebay.de",
}
EBAY_BY_AREA = {
    "EU": "www.ebay.de", "UKTERR": "www.ebay.co.uk", "FRTERR": "www.ebay.fr",
    "AUTERR": "www.ebay.com.au",
}

# ---------- Facebook Marketplace ----------
# Each one checked by loading it (September 2026): Facebook sends an unknown city somewhere else without
# saying so. Countries missing here either have no Marketplace (Japan) or a city Facebook only knows by
# number; the user types their own city in Settings.
FACEBOOK_CITY = {
    "GB": "london", "IE": "dublin", "AU": "sydney", "NZ": "auckland",
    "DE": "berlin", "FR": "paris", "IT": "rome", "ES": "madrid", "PT": "lisbon", "NL": "amsterdam",
    "BE": "brussels", "CH": "zurich", "AT": "vienna", "SE": "stockholm", "NO": "oslo", "DK": "copenhagen",
    "FI": "helsinki", "PL": "warsaw", "CZ": "prague", "SK": "bratislava", "HU": "budapest",
    "RO": "bucharest", "BG": "sofia", "GR": "athens", "HR": "zagreb", "TR": "istanbul", "UA": "kyiv",
    "LT": "vilnius", "LV": "riga", "IS": "reykjavik", "LU": "luxembourg", "MT": "valletta", "CY": "nicosia",
    "IL": "telaviv", "AE": "dubai", "SA": "riyadh", "QA": "doha", "BH": "manama", "OM": "muscat",
    "JO": "amman", "LB": "beirut", "EG": "cairo", "ZA": "johannesburg", "NG": "lagos", "KE": "nairobi",
    "GH": "accra", "MA": "casablanca", "TN": "tunis", "IN": "mumbai", "BD": "dhaka", "LK": "colombo",
    "SG": "singapore", "MY": "kualalumpur", "PH": "manila", "TH": "bangkok", "ID": "jakarta",
    "VN": "hochiminhcity", "KR": "seoul", "TW": "taipei", "HK": "hongkong", "MX": "mexicocity",
    "BR": "saopaulo", "AR": "buenosaires", "CL": "santiago", "CO": "bogota", "PE": "lima", "EC": "quito",
    "UY": "montevideo", "PY": "asuncion", "BO": "lapaz", "VE": "caracas", "PA": "panamacity",
    "GT": "guatemalacity", "DO": "santodomingo", "PR": "sanjuan",
}
# Facebook is blocked or Marketplace does not run in these.
NO_MARKETPLACE = {"CN", "KP", "IR", "RU", "JP", "TM"}

# English locales the browser can present itself with; everywhere else uses the nearest general one.
KNOWN_EN_LOCALES = {"US", "GB", "CA", "AU", "NZ", "IE", "IN", "SG", "ZA", "PH", "HK", "MY", "NG", "KE", "PK"}


def name(code: str) -> str:
    return COUNTRIES.get(code, (code,))[0]


def currency(code: str) -> str:
    return COUNTRIES.get(code, ("", "USD"))[1]


def area(code: str) -> str:
    return COUNTRIES.get(code, ("", "", ""))[2]


def selectable(code) -> bool:
    """Can the country setting be this? Every country but the two the other edition covers."""
    return code in COUNTRIES and code not in OTHER_EDITION


def amazon_site(code: str):
    """The Amazon domain that serves this country, or None where Amazon does not sell."""
    if code in EMBARGOED or not selectable(code):
        return None
    return AMAZON_OWN.get(code) or AMAZON_NEAR.get(code) or AMAZON_BY_AREA.get(area(code)) or "amazon.com"


def ebay_site(code: str):
    """The eBay host that serves this country, or None where eBay does not sell."""
    if code in EMBARGOED or not selectable(code):
        return None
    return EBAY_OWN.get(code) or EBAY_NEAR.get(code) or EBAY_BY_AREA.get(area(code)) or "www.ebay.com"


def browser_locale(code: str) -> str:
    if code in KNOWN_EN_LOCALES:
        return f"en-{code}"
    return "en-GB" if area(code) in ("EU", "EUROPE", "UKTERR", "AFRICA", "MENA", "GULF", "OCEANIA") else "en-US"


def sort_key(text: str) -> str:
    """'Åland Islands' files under A and 'Côte d'Ivoire' under C, as a reader expects."""
    import unicodedata
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def listing():
    """Every country for the settings menu, sorted by name."""
    return sorted(({"code": c, "name": v[0], "currency": v[1]} for c, v in COUNTRIES.items() if selectable(c)),
                  key=lambda c: sort_key(c["name"]))


def detect():
    """This computer's country from the operating system's region setting, or None if it cannot tell."""
    import sys
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(16)
            if ctypes.windll.kernel32.GetUserDefaultGeoName(buf, len(buf)) and buf.value.upper() in COUNTRIES:
                return buf.value.upper()
        except Exception:
            pass
    import locale
    import os
    for raw in (locale.getlocale()[0], os.environ.get("LC_ALL"), os.environ.get("LANG")):
        tail = (raw or "").split(".")[0].replace("-", "_").split("_")
        if len(tail) >= 2 and tail[-1].upper() in COUNTRIES:
            return tail[-1].upper()
    return None
