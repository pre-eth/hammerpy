from types import FunctionType
from math import ceil, floor
from PIL import Image, ImageTk
from time import sleep
from urllib.request import urlretrieve
from re import sub
from datetime import date
from os import mkdir, path
from threading import Thread
from queue import Queue, Empty
from os import remove, path

from tkinter import IntVar
from tkinter.ttk import Label

from hammerpy.gui import Guesswork, HammerPy

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

# separate function in separate thread from HammerPy
# because main thread must run GUI
def update_status(h: HammerPy, q: Queue, limit: int):
  disp_height = h.height - 200
  factor = (0.05 + (0.1 * h.difficulty.get()))
  review_width = 500

  while True:
    try:
      item = q.get()
    except Empty:
      continue

    if not item:
      break
    
    # determine other properties for this work and construct Guesswork object

    work, save_path = item

    # determine dimensions for showing image in guess and result screens
    # IF THE IMAGE OBJECT ISN'T READ ALL AT ONCE HERE IT DOESN'T LOAD
    with Image.open(save_path) as img: 
      width = img.width
      height = img.height
      disp_width = float(float(width) / float(height)) * float(disp_height)
      size1 = img.resize((ceil(disp_width), disp_height))
      tk_img = ImageTk.PhotoImage(image=size1)

      review_height = 500.0 / (float(width) / float(height))
      size2 = img.resize((review_width, ceil(review_height)))
      tk_img2 = ImageTk.PhotoImage(image=size2)
    
    lower_bound = floor(work.prices[0] * (1.0 - factor))
    upper_bound = floor(work.prices[1] * (1.0 + factor))
    
    keep = IntVar()
    keep.set(0)

    guess_work = Guesswork(work, save_path, tk_img, tk_img2, ceil(disp_width), disp_height, 
                           review_width, ceil(review_height), lower_bound, upper_bound, keep)

    h.works.append(guess_work)
    h.loading["text"] = f"Fetching artworks... ({len(h.works)}/{limit})\n"
  
  # Queue has been read in full, start the actual guessing game
  h.start_game()

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

