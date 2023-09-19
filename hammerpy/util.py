from types import FunctionType
from time import sleep
from urllib.request import urlretrieve
from re import sub
from datetime import date
from os import mkdir, path
from threading import Thread
from queue import Queue
from tkinter.ttk import Label

def switch_desc(diff_desc: Label, descs: list[str], diff_int: int):
  diff_desc["text"] = descs[diff_int]

def switch_limit(quantity: Label, current_limit: int):
  new_limit = int(float(current_limit))
  quantity["text"] = f"{new_limit}".zfill(2)

def cleanse(sins):
  return sub("[?:/\"\'\t\n\r!@#$%&<>{}|=+`]", "", sins)

class Scraper(Thread):
  def __init__(self, queue: Queue, limit: int, scrape_fn: FunctionType):
    super().__init__()
    self._running = True            # sentinel to track whether user/program has terminated thread
    self.daemon = True              # mark thread as daemon so it runs in bg, stops on program close
    self._q = queue                 # Message queue for sharing downloaded works to a consumer thread
    self._limit = limit             # how many artworks to scrape
    self._scrape = scrape_fn        # source to scrape

  def stop(self):
    self._running = False
  
  def run(self):
    count = 0

    # neatly organize images into folders per day for different "sessions"
    today_date = date.today()
    if not path.isdir(f"img/{today_date}"):
      mkdir(f"img/{today_date}")
    
    while self._running and count < self._limit:
      work = self._scrape()
      
      final_title = cleanse(work.title)
      save_path = f"img/{today_date}/{final_title}.jpg"
      urlretrieve(work.image, save_path)

      count += 1
      self._q.put_nowait((work, save_path))
      if count == 5:
        sleep(5)

    self._q.put_nowait(None)

