from selenium import webdriver
from selenium.webdriver.common.by import By
from random import choice, randint
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

def scrape_sothebys(url: str, driver: webdriver) -> Artwork:
  driver.get(url)

  # let things load
  sleep(3)

  items = driver.find_element(By.TAG_NAME, "ul")
  
  works = items.find_elements(By.TAG_NAME, "li")
  idx = randint(0, len(works) - 1)
  work = driver.find_element(By.ID, f"tilePositionIndex={idx}")
  
  img = work.find_elements(By.XPATH, "//div[1]/span/img")[0]
  img_url = img.get_attribute("src")
  
  title = work.find_element(By.TAG_NAME, "h5").text

  title += ' ' + work.find_elements(By.TAG_NAME, "p")[0].text

  price = work.find_elements(By.TAG_NAME, "p")[1].text.replace(',', '')
  price = price[:-4]

  driver.get(img_url)
  sleep(3)
  img_url = driver.current_url
  cutoff = img_url.index("?url=") + 5
  img_url = unquote(img_url[cutoff:])

  return Artwork(title, img_url, [int(price), int(price)])

