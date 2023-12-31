from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from random import randint
from requests import get
from urllib.parse import unquote
from enum import Enum
from json import loads
from gzip import decompress
from array import array

from hammerpy.util import Artwork

# Sotheby's has a WIDE breadth of items
#
# We start by declaring all the different categories
# and assign their URL slugs as their values
class Category(Enum):
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
  from selenium.webdriver.common.by import By
  from selenium.webdriver.support.ui import WebDriverWait
  from selenium.webdriver.support import expected_conditions as EC

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

def scrape_sothebys(cat: str, amount: int) -> (list[Artwork], bool):
  agent = "Mozilla/5.0 (Windows Phone 10.0; Android 6.0.1; Microsoft; RM-1152) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Mobile Safari/537.36 Edge/15.15254"
  slug = Category[cat].value
  scrape_url = f"https://www.sothebys.com/en/buy/{slug}"
  
  pagemax = 0
  
  with open("hammerpy/sothpmax", "rb") as file:
    pmax_arr = array('B')
    pmax_arr.fromfile(file, len(Category))
    idx = list(name for name, _ in Category.__members__.items()).index(cat)
    pagemax = pmax_arr[idx]
    
  # if no pagemax recorded for category, or stored pagemax fails diagnostic test
  if not pagemax:
    pagemax = get_page_limit(scrape_url, pmax_arr, idx)

  scrape_url = f"{scrape_url}?page={randint(1,pagemax)}"
  options = Options()
  options.add_argument(f"--user-agent={agent}")
  options.add_argument("--headless")
  driver = webdriver.Chrome(options=options)

  print(f"LAUNCHING {scrape_url}...")
  driver.get(scrape_url)

  items = []
  works = []

  # inspect Sotheby's GraphQL requests, and decode the data to JSON
  for request in driver.requests:
    if request.url.startswith("https://kar1ueupjd-dsn.algolia.net/1/indexes/*/queries") and request.response:
      json_str = decompress(request.response.body).decode('utf8')
      items = loads(json_str)["results"][0]["hits"]
      break
  
  driver.quit()
  results = len(items)

  # Randomly select and get metadata for items
  for _ in range(amount):
    idx = randint(1, results)  

    work = items[idx]

    # Get Artwork members
    title = work["title"]
    lower_bound = work["lowEstimate"]
    upper_bound = work["highEstimate"]
    img_url = work["imageUrl"]

    # Retrieve full resolution image
    cutoff = img_url.index("?url=") + 5
    img_url = unquote(img_url[cutoff:])

    works.append(Artwork(title, img_url, [lower_bound, upper_bound]))
    items.remove(work)
    if not items:
      break

  return (works, pagemax == 1 and results < amount)

