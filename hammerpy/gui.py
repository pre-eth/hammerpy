from dataclasses import dataclass
from math import ceil, floor
from PIL import Image, ImageTk
from tkinter import StringVar, IntVar, Canvas
from tkinter.ttk import Frame, Label, Style, Scale, Button, Radiobutton, Entry
from queue import Queue, Empty
from threading import Thread
from os import remove, path

from hammerpy.artsy import scrape_artsy, Artwork

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
  def keep(self, value: bool):
    self._keep.set(value)

  @property
  def guess(self):
    return self._guess

  @guess.setter
  def guess(self, value: int):
    self._guess = value


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
    print(guess_work)

    h.works.append(guess_work)
    h.loading["text"] = f"Fetching artworks... ({len(h.works)}/{limit})\n"
  
  # Queue has been read in full, start the actual guessing game
  h.start_game()

def remove_works(works: list[Guesswork]):
  for w in works:
    if not w.keep.get() and path.isfile(w.path):
      remove(w.path)