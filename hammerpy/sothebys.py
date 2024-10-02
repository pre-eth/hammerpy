"""Scrapes Artwork instances from the historic auction house of Sotheby's"""

from random import randint
from urllib.parse import unquote
from enum import Enum
from json import loads
from gzip import decompress
from array import array

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

from hammerpy.util import Artwork
from hammerpy.artsy import AGENTP1, AGENTP2


# Sotheby's has a WIDE breadth of items
#
# We start by declaring all the different categories
# and assign their URL slugs as their values
class Category(Enum):
    """For allowing the user to choose a scraping category."""

    ALL = "shop-all"
    JEWELRY = "luxury/jewelry"
    WATCHES = "luxury/watches"
    HANDBAGS = "fashion/handbag"
    BOOKS = "luxury/books-&-manuscripts"
    ART = "art-&-design"
    COLLECTIBLES = "luxury/collectibles"
    CARS = "luxury/vehicles/car"
    INTERIORS = "interiors"
    APPAREL = "fashion/apparel"
    SNEAKERS = "fashion/sneaker"


def get_page_limit(url: str, pmax_arr: array, idx: int) -> int:
    """Dynamically determines the max number of pages for a search."""

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # to get the page limit for this category, we read
    # the second to last element of pagination
    last_li = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "nav"))
    )
    pages = last_li.find_elements(By.TAG_NAME, "li")
    if len(pages) == 1:
        pmax = 1
    else:
        pmax = int(pages[-2].text)

    pmax_arr[idx] = pmax

    # Write to file so next time we don't need to do all this
    with open("hammerpy/sothpmax", "wb+") as file:
        pmax_arr.tofile(file)

    driver.quit()
    return pmax


def scrape_sothebys(cat: str, amount: int) -> tuple[list[Artwork], bool]:
    """Main scraping routine for extracting Artwork."""

    scrape_url = f"https://www.sothebys.com/en/buy/{Category[cat].value}"

    pagemax = 0

    with open("hammerpy/sothpmax", "rb") as file:
        pmax_arr = array("B")
        pmax_arr.fromfile(file, len(Category))
        idx = list(name for name, _ in Category.__members__.items()).index(cat)
        pagemax = pmax_arr[idx]

    # if no pagemax recorded for category, or stored pagemax fails diagnostic test
    if not pagemax:
        pagemax = get_page_limit(scrape_url, pmax_arr, idx)

    scrape_url = f"{scrape_url}?page={randint(1,pagemax)}"
    options = Options()
    options.add_argument(f"--user-agent='{AGENTP1} {AGENTP2}'")
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    print(f"LAUNCHING {scrape_url}...")
    driver.get(scrape_url)

    items = []
    works = []

    # inspect Sotheby's GraphQL requests, and decode the data to JSON
    for request in driver.requests:
        if (
            request.url.startswith(
                "https://kar1ueupjd-dsn.algolia.net/1/indexes/*/queries"
            )
            and request.response
        ):
            items = loads(decompress(request.response.body).decode("utf8"))
            break

    driver.quit()
    items = items["results"][0]["hits"]
    results = len(items)

    # Randomly select and get metadata for items
    for _ in range(amount):
        work = items[randint(1, results)]

        # Get Artwork members
        img_url = work["imageUrl"]

        # Retrieve full resolution image
        img_url = unquote(img_url[img_url.index("?url=") + 5 :])

        works.append(
            Artwork(work["title"], img_url, [work["lowEstimate"], work["highEstimate"]])
        )
        items.remove(work)
        if not items:
            break

    return (works, pagemax == 1 and results < amount)
