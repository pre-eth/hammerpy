from dataclasses import dataclass
from types import FunctionType
from PIL import ImageTk
from time import sleep
from urllib.request import urlretrieve
from re import sub
from datetime import date
from os import mkdir, path
from random import randint
from threading import Thread
from queue import Queue
from os import remove, path

from tkinter import IntVar
from tkinter.ttk import Label

@dataclass
class Artwork():
  title: str
  image_url: str
  prices: list[int]

@dataclass
class Guesswork():
  art: Artwork
  path: str
  disp_img: ImageTk.PhotoImage
  review_img: ImageTk.PhotoImage
  disp_width: int
  disp_height: int
  review_width: int
  review_height: int
  lower_bound: int
  upper_bound: int
  _keep: IntVar
  _guess: int = 0

  @property
  def keep(self):
    return self._keep

  @keep.setter
  def keep(self, value: int):
    self._keep.set(value)

  @property
  def guess(self):
    return self._guess

  @guess.setter
  def guess(self, value: int):
    self._guess = value

class Scraper(Thread):
  def __init__(self, queue: Queue, limit: int, src_type: int, slug: str, scrape_fn: FunctionType):
    super().__init__()
    self._running = True            # sentinel to track whether user/program has terminated thread
    self.daemon = True              # mark thread as daemon so it runs in bg, stops on program close
    self._q = queue                 # Message queue for sharing downloaded works to a consumer thread
    self._limit = limit             # how many artworks to scrape
    self._src_type = src_type       # whether source to scrape is Artsy (0) or Sotheby's (1)
    self._scrape = scrape_fn        # source to scrape
    self._slug = slug               # filter that user wants to apply to results
    self.driver = None

  def stop(self):
    self._running = False
  
  def run(self):
    count = 0

    # neatly organize images into folders per day for different "sessions"
    today_date = date.today()
    if not path.isdir(f"img/{today_date}"):
      mkdir(f"img/{today_date}")

    work = None
    scrape_url = ""
    pagemax = 100
    if self._src_type:
      from selenium import webdriver
      from selenium.webdriver.chrome.options import Options
      from selenium.webdriver.common.by import By

      scrape_url = f"https://www.sothebys.com/en/buy/{self._slug}"
      options = Options()
      options.add_argument('--disable-blink-features=AutomationControlled')
      options.add_argument("--headless")
      self.driver = webdriver.Chrome(options=options)
      
      self.driver.get(scrape_url)
      sleep(3)
      # we start by getting the page limit for this category
      # need to read second to last element of pagination
      last_li = self.driver.find_element(By.TAG_NAME, "nav")
      pages = last_li.find_elements(By.TAG_NAME, "li")[-2]
      pagemax = int(pages.text) 
    else:
      scrape_url = f"https://www.artsy.net/collect{self._slug}"

    while self._running and count < self._limit:
      url = f"{scrape_url}?page={randint(1, pagemax + 1)}"
      
      if self._src_type:
        work = self._scrape(url, self.driver)
      else:
        work = self._scrape(url)
      
      # print(work)
      final_title = cleanse(work.title)
      save_path = f"img/{today_date}/{final_title}.jpg"
      urlretrieve(work.image_url, save_path)

      count += 1
      self._q.put_nowait((work, save_path))
      if count == 5:
        sleep(5)
    
    if self._src_type:
      self.driver.quit()

    self._q.put_nowait(None)

def switch_desc(diff_desc: Label, descs: list[str], diff_int: int):
  diff_desc["text"] = descs[diff_int]

def switch_limit(quantity: Label, current_limit: int):
  new_limit = int(float(current_limit))
  quantity["text"] = f"{new_limit}".zfill(2)

def cleanse(sins):
  return sub("[?:/\"\'\t\n\r!@#$%&<>{}|=+`]", "", sins)

def remove_works(works: list[Guesswork]):
  for w in works:
    if not w.keep.get() and path.isfile(w.path):
      remove(w.path)


