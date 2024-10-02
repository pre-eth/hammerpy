"""Scrapes Artwork instances from the popular auction exchange Artsy.net."""

from math import floor
from re import sub, findall
from random import choice, randint
from urllib.parse import unquote
from enum import Enum

from requests import get
from requests.exceptions import Timeout
from bs4 import BeautifulSoup
from hammerpy.util import Artwork


# Create enum to represent different artwork mediums
class Medium(Enum):
    "Enum to track the different types of art available on the website."

    ALL = ""
    PAINTING = "ion/painting"
    PRINTS = "ion/prints"
    PHOTOGRAPHY = "ion/photography"
    SCULPTURE = "ion/sculpture"
    WORKS_ON_PAPER = "ion/works-on-paper"
    DESIGN = "ion/design"
    MIXED_MEDIA = "ion/mixed-media"

# User agent
AGENTP1 = "Mozilla/5.0 (Windows Phone 10.0; Android 6.0.1; Microsoft; RM-1152) AppleWebKit/537.36"
AGENTP2 = "(KHTML, like Gecko) Chrome/52.0.2743.116 Mobile Safari/537.36 Edge/15.15254"

# for lookup with currency api, tried to include most of the major ones
CURRENCIES = {
    "C$": "cad",
    "€": "eur",
    "£": "gbp",
    "HK$": "hkd",
    "¥": "jpy",
    "ZAR": "zar",
    "CN¥": "cny",
    "BRL": "brl",
    "₱": "php",
    "KRW ₩": "krw",
}

# URL prefix for scraping
PREFIX = "https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/usd/"

# max number of pages that will be searched
PAGEMAX = 100

def scrape_artsy(slug: str, amount: int) -> tuple[list[Artwork], bool]:
    """The main scraper function itself."""

    l = 0
    works = []
    while not l:
        # pick a random page and get its content
        url = f"https://www.artsy.net/collect{slug}?page={randint(1,PAGEMAX)}"
        try:
            dump = get(url, data={"User-Agent": f"{AGENTP1} {AGENTP2}"}, timeout=10)
        except Timeout:
            continue

        # artworkGridItem is identifier for any work on the page, we choose a random one
        artdivs = BeautifulSoup(dump.text, "html.parser")
        artdivs = artdivs.find_all("div", attrs={"data-test": "artworkGridItem"})
        if not artdivs:
            continue

        for i in range(amount):
            div = choice(artdivs)

            price = div.findNext("div", attrs={"font-weight": "bold"})
            price = price.text.replace(",", "")

            # get the image
            img_tag = div.findNext("img")

            # check if fullsize url is available
            imgurl = img_tag.get("src")
            img = imgurl[imgurl.index("https%") : imgurl.rindex(".jpg") + 4]
            img = unquote(sub("(larger?)", "normalized", img))

            # check for HTTPError for fullsized url cause it uses the keyword 'normalized'
            # if unavailable try a different work
            if get(img, timeout=10).status_code != 200:
                artdivs.remove(div)
                continue

            work_prices = []
            if price.startswith("US$"):
                price = price.replace("US$", "").replace(",", "")
                price = price.replace("–", "-").strip()

                prices = price.split("-")
                work_prices.append(int(prices[0]))
                work_prices.append(int(prices[-1]))

            # find non US currency symbol, search in dict,
            # if found look up in api to get conversion rate for USD
            elif intl_money := [c for c in CURRENCIES if price.startswith(c)]:
                # exchange rate lookup for foreign currencies
                prices = findall(r"((\d,*)+)", price)
                p1 = p2 = int(prices[0][0].replace(",", ""))
                rate_json = get(f"{CURRENCIES[intl_money[0]]}.json", timeout=10).json()

                exchange_rate = float(rate_json[CURRENCIES[intl_money[0]]])

                # no hyphen means first price is same as "second" price
                work_prices.append(floor(p1 / exchange_rate))

                # hyphen indicates price RANGE, so need to convert 2nd price as well
                if "-" in price:
                    p2 = int(prices[1][0].replace(",", ""))
                    work_prices.append(floor(p2 / exchange_rate))
            else:
                # if currency is not found or it's a phrase like "contact for price",
                # "sold", etc - oh well pick another artwork
                continue

            # format title into "name - 'work' (date)"
            title = img_tag.get("alt").replace(",", " -", 1)
            title = (
                title.replace(title[title.rindex(",") : title.rindex(",") + 2], " (")
                + ")"
            )

            works.append(Artwork(title, img, work_prices))
            artdivs.remove(div)
            if not artdivs:
                break

        # check if there was enough results on page to satisfy quota
        # if not, pick another random page and start again
        if i == amount - 1:
            l = 1
        else:
            amount -= i

    return (works, False)
