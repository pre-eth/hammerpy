from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from random import randint
from urllib.parse import unquote
from time import sleep
from enum import Enum

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
  CARS = "luxury/vehicles"
  INTERIORS = "interiors"
  APPAREL = "fashion/apparel"
  SNEAKERS = "fashion/sneaker"

def scrape_sothebys(url: str, driver: webdriver.Firefox) -> Artwork:
  driver.get(url)
  # let things load
  sleep(5)

  items = driver.find_element(By.TAG_NAME, "ul").find_elements(By.TAG_NAME, "li")
  count = randint(1, 4)
  past = []
  works = []

  for _ in range(count):
    idx = randint(1, len(items))  
    if idx in past:
      if idx + 1 < len(items):
        idx += 1
      elif idx - 1 < len(items):
        idx -= 1

    work = driver.find_element(By.ID, f"tilePositionIndex={idx}")
    soup = BeautifulSoup(work.get_attribute("innerHTML"), "html.parser")
    # print("id:", idx)
    # print(work.get_attribute("innerHTML")) 

    img = soup.find("img")
    img_url = img["src"]
    # print(img_url)
    
    # Title and price info
    title = "" 
    if soup.h5:
      title += soup.h5.text + ' '
    title += soup.p.text
    price = soup.find_all('p')[1].text.replace(',', '')[:-4]

    # Retrieve real image url
    driver.get(img_url)
    sleep(5)
    img_url = driver.current_url
    cutoff = img_url.index("?url=") + 5
    img_url = unquote(img_url[cutoff:])

    works.append(Artwork(title, img_url, [int(price), int(price)]))
    past.append(idx)

  return works

