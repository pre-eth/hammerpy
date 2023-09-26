from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from requests import get
from bs4 import BeautifulSoup
from math import floor
from re import sub, findall
from random import choice, randint
from urllib.parse import unquote
from enum import Enum

from hammerpy.util import Artwork

# Sotheby's has a WIDE breadth of items
#
# We start by declaring all the different categories
# and assign their URL slugs as their values
class Category(Enum):
    RANDOM = "shop-all"
    JEWELRY = "luxury/jewelry"
    WATCHES = "fashion/handbag"
    HANDBAGS = "watches/watch"
    BOOKS = "luxury/books-&-manuscripts"
    ART = "art-&-design"
    COLLECTIBLES = "luxury/collectibles"
    CARS = "luxury/vehicles"
    INTERIORS = "interiors"
    APPAREL = "fashion/apparel"
    SNEAKERS = "fashion/sneaker"

def scrape_sothebys() -> Artwork:
    pass
