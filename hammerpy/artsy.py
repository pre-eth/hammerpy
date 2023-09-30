from requests import get
from bs4 import BeautifulSoup
from math import floor
from re import sub, findall
from random import choice, randint
from urllib.parse import unquote
from enum import Enum

from hammerpy.util import Artwork
 
# Create enum to represent different artwork mediums
class Medium(Enum):
  ALL = ""
  PAINTING = "ion/painting"
  PRINTS = "ion/prints"
  PHOTOGRAPHY = "ion/photography"
  SCULPTURE = "ion/sculpture"
  WORKS_ON_PAPER = "ion/works-on-paper"
  DESIGN = "ion/design"
  MIXED_MEDIA = "ion/mixed-media"

def scrape_artsy() -> Artwork:
  agent = "Mozilla/5.0 (Windows Phone 10.0; Android 6.0.1; Microsoft; RM-1152) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Mobile Safari/537.36 Edge/15.15254"
 
  # max number of pages that will be searched
  pagemax = 100         
 
  # for lookup with currency api, tried to include most of the major ones
  currencies = {"C$":"cad","€":"eur","£":"gbp","HK$":"hkd","¥":"jpy",
                "ZAR":"zar","CN¥":"cny","BRL":"brl","₱":"php"}

  l = 0
  while not l:
    # pick a random page and get its content      
    link = f"https://www.artsy.net/collect?page={randint(1, pagemax)}"
    dump = get(link, data={"User-Agent" : agent})
    dump = BeautifulSoup(dump.text, "html.parser")

    # artworkGridItem is identifier for any work on the page, we choose a random one
    artdivs = dump.find_all("div", attrs={"data-test":"artworkGridItem"})
    if not artdivs:
      continue
    div = choice(artdivs)
    price = div.findNext("div", attrs={"font-weight":"bold"}).text.replace(',','')

    # get the image
    img_tag = div.findNext('img')

    # check if fullsize url is available
    imgurl = img_tag.get("src")
    img = imgurl[imgurl.index("https%"):imgurl.rindex(".jpg")+4]
    img = sub("(larger?)", "normalized", img)
    img = unquote(img)

    # check for HTTPError for fullsized url cause it uses the keyword 'normalized'
    # if unavailable try a different work
    if get(img).status_code != 200:
      artdivs.remove(div)
      continue

    work_prices = []
    # find non US currency symbol, search in dict, 
    # if found look up in api to get conversion rate for USD
    if price.startswith("US$"):       
      price = price.replace("US$",'').replace(',', '').replace('–', '-').strip()

      prices = price.split('-')
      work_prices.append(int(prices[0]))
      idx = len(prices) > 1
      work_prices.append(int(prices[idx]))
    else:
      intl_money = [c for c in currencies if price.startswith(c)]
      if intl_money:
        # exchange rate lookup for foreign currencies 
        prices = findall(r"((\d,*)+)", price)
        p1 = int(prices[0][0].replace(',', ''))
        curr = intl_money[0]
        currency = currencies[curr]
        rate_json = get(f"https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/usd/{currency}.json").json()
        
        exchange_rate = float(rate_json[currency])

        # no hyphen means first price is same as "second" price
        work_prices.append(floor(p1 / exchange_rate))
        p2 = p1 

        # hyphen indicates price RANGE, so need to convert 2nd price as well
        if '-' in price:
          p2 = int(prices[1][0].replace(',', ''))
        
        work_prices.append(floor(p2 / exchange_rate))
      else:
        # if currency is not found or it's a phrase like "contact for price", 
        # "sold", etc - oh well pick another artwork
        continue

    # format title into "name - 'work' (date)"
    title = img_tag.get("alt").replace(',', ' -', 1)
    title = title.replace(title[title.rindex(','):title.rindex(',')+2], ' (')+')' 
    
    work = Artwork(title, img, work_prices)
    # to make sure we don't flood Artsy with requests and cause us to get blocked
    l = 1

  return work
