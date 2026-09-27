# Item Hunter International

A local price watcher for PC parts, for every country outside Canada and the United States. Add a
part (for example `9950X3D`), and Item Hunter searches the stores that sell where you live, on a
timer, using your own PC and your installed Edge or Chrome browser. When a listing gets cheaper,
or a new listing appears below your current best price, it shows up in the feed and you get a
notification you can click to open the listing. Only in-stock listings are shown.

Pick your country in Settings (it starts on the country Windows is set to), and the app switches
stores, currency and Facebook city to match.

**In Canada or the United States?** Use [Item Hunter for Canada and the US](https://github.com/Lemypoo/PC-Hunter-Bot-US-CANADA)
instead. It also watches the retailers there (Newegg, Best Buy Canada, Canada Computers).

## Which stores, where

| Store | Countries |
| --- | --- |
| Amazon | Its own site in 21 countries: UK, Ireland, Germany, France, Italy, Spain, Netherlands, Belgium, Sweden, Poland, Türkiye, UAE, Saudi Arabia, Egypt, India, Japan, Australia, Singapore, South Africa, Mexico, Brazil. Everywhere else, the nearest one that sells to you: Amazon.de for most of Europe, Amazon.es for Portugal, Amazon.com.au for New Zealand, Amazon.ae for the Gulf, Amazon.com for the rest. |
| eBay | Its own site in 16 countries: UK, Germany, France, Italy, Spain, Australia, Austria, Switzerland, Ireland, Belgium, Netherlands, Poland, Hong Kong, Singapore, Malaysia, Philippines. Everywhere else, eBay.de (EU), eBay.com.au (New Zealand) or eBay.com. |
| Facebook Marketplace | Nearly everywhere, near the city you set. 75 countries come with a checked default city. Not available in Japan, China, Russia, Iran, North Korea or Turkmenistan. |

Amazon and eBay are not offered in countries under sanctions (Cuba, Iran, North Korea, Russia,
Belarus, Syria). When a store is served from another country, Settings says so: check that an item
ships to you, and outside the EU the price does not include import fees.

Amazon pages are requested in English wherever the marketplace has an English version, which is
what the page reader understands best.

## Currencies

Every price is shown in the currency the store or seller used. Comparisons (best price, alerts,
target, min and max) happen in your country's currency, so Amazon.de in euros and eBay.ch in francs
can be compared directly. A listing in another currency also shows roughly what it comes to at home.

Exchange rates come from open.er-api.com (ExchangeRate-API), with a second free source as backup,
at most twice a day and only when some listing needs converting. They are cached in
`data/rates.json`. Until a rate is available, a foreign-priced listing is shown but never counts as
the best price and never raises an alert.

## Run

Double-click `start.bat`, or:

```
python app.py
```

Your browser opens at http://127.0.0.1:8787/. Leave the window running. Each store is checked on
its own clock, and two stores are read at the same time. At Normal speed that is eBay every 4
minutes, Facebook every 5 and Amazon every 15. Settings has a Fast / Normal / Relaxed switch that
scales all of them, and the number of stores read at once (1 to 4, takes effect after a restart).
Amazon stays slow on purpose: it starts refusing a home connection that searches it often.

## Requirements

Python 3.10+ with `pip install -r requirements.txt`. Scraping uses Microsoft Edge (already on
Windows) or Chrome. If neither is installed, run `playwright install chromium` once. On macOS or
Linux, start it with `python3 app.py`; the desktop notification is Windows-only, but email and
phone push work everywhere.

## Phone alerts

Settings has two optional channels besides the Windows notification, both with a test button:

- **Email**: enter the address to notify plus an account to send from. Gmail and Outlook
  need a 16-character app password, not the normal one (Gmail: smtp.gmail.com port 587;
  Outlook: smtp.office365.com port 587).
- **Phone push**: install the free ntfy app, press "Generate topic", subscribe to that topic in
  the app, and alerts arrive as push notifications within seconds. No account needed.

Every channel uses the same rule: a listing that beats an item's best price, drops to within
5% of it, or reaches the item's target price. At most three alerts per store per check.

## Used and open-box offers

Amazon sells used and open-box stock through other sellers on every marketplace, and through
Amazon Resale (formerly Warehouse Deals) on Amazon.co.uk, .de, .fr, .it and .es, and on Amazon.com.
Item Hunter reads the "used & new offers" line on the search page and, where it exists, the Resale
storefront, and shows the cheapest such offer for a product as its own row marked "used". Turn it
off in Settings with "Include used and open-box offers" to watch new-in-box prices only.

## Facebook city

Open Facebook Marketplace in your own browser, pick your city, and copy the word after
`/marketplace/` in the address bar (`london`, `kualalumpur`, `saopaulo`). Some cities only have a
long number there; that works too. If Facebook does not know the name, it quietly shows a different
city; Item Hunter notices and says so instead of searching the wrong place.

## Tips

- Keep the search short: `9950X3D`, `RTX 5080`, `9800X3D`. Every word you type must appear
  in a listing's title for it to count. Edit the "must contain" and "exclude" lists per item.
- Prebuilt PCs and bundles are excluded by default (words like "gaming pc", "bundle"). A CPU
  search also ignores motherboards and graphics cards; a GPU search ignores CPUs, chipsets, cases,
  mounts and power supplies "ready for" the card. Set a max price on the item to cut the rest.
- A marketplace listing far below every retail price (the "message me" kind) is tagged "price?"
  and never counts as the best price or triggers a notification.
- If a store blocks the automated browser, a red chip names it at the top of the page and the
  app leaves that store alone for 30 minutes before trying again. If a store keeps blocking, set
  the speed to Relaxed.
- Switching country keeps the old country's listings stored but out of sight, so switching back
  brings them back.

## Your data

Everything lives in the `data` folder: `state.json` holds your items, price history and
settings (including the SMTP password, in plain text), `state.json.bak` is the previous copy
that the app recovers from if the live file is ever damaged, `rates.json` holds exchange rates,
and the `browser_state` files are the stores' cookies. The folder is in `.gitignore`, so none of
it ends up on GitHub.

## Tests

```
python tests/test_hunter.py
```

About 160 checks covering matching, price formats from around the world, every country's store
setup, currency conversion, moving between countries, Amazon page detection, alerts, the state
file and the parallel checkers. None of them touch the network.
