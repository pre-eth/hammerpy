"""General purpose utilities and helpers for smooth game operation."""

from dataclasses import dataclass
from types import FunctionType
from time import sleep
from urllib.request import urlretrieve
from re import sub
from datetime import date
from os import mkdir, remove, path
from random import randint
from threading import Thread
from queue import Queue
from array import array
from tkinter import IntVar
from tkinter.ttk import Label

from PIL import ImageTk

from hammerpy.sothebys import Category


@dataclass
class Artwork:
    """Represents a piece of artwork scraped from the internet."""

    title: str
    image_url: str
    prices: list[int]


@dataclass
class Guesswork:
    """Represents an Artwork instance with additional guessing-related metrics."""

    art: Artwork
    path: str
    disp_img: ImageTk.PhotoImage
    disp_width: int
    disp_height: int
    review_img: ImageTk.PhotoImage
    review_width: int
    review_height: int
    lower_bound: int
    upper_bound: int
    _keep: IntVar
    _guess: int = 0

    @property
    def keep(self):
        """Flag for tracking whether we should keep the image file on the user's computer."""

        return self._keep

    @keep.setter
    def keep(self, value: int):
        self._keep.set(value)

    @property
    def guess(self):
        """Get the user's current price estimation."""

        return self._guess

    @guess.setter
    def guess(self, value: int):
        self._guess = value


class Scraper(Thread):
    """Handles collection of artwork."""

    def __init__(
        self,
        queue: Queue,
        limit: int,
        src_type: int,
        slug: str,
        scrape_fn: FunctionType,
    ):
        super().__init__()
        self._running = (
            True  # sentinel to track whether user/program has terminated thread
        )
        self.daemon = (
            True  # mark thread as daemon so it runs in bg, stops on program close
        )
        self._q = (
            queue  # Message queue for sharing downloaded works to a consumer thread
        )
        self._limit = limit  # how many artworks to scrape
        self._scrape = scrape_fn  # source to scrape
        self._slug = slug  # filter that user wants to apply to results
        self.driver = None

        # Does the Sotheby's page max binary file exist? If not, then create it
        if src_type and not path.isfile("hammerpy/sothpmax"):
            with open("hammerpy/sothpmax", "wb+") as file:
                pmax_arr = array("B", [0] * len(Category))
                pmax_arr.tofile(file)

    def stop(self):
        """Stop the scraping preocedure."""

        self._running = False

    def run(self):
        """Run the scraping preocedure."""

        count = 0
        works = []

        # neatly organize images into folders per day for different "sessions"
        today_date = date.today()
        if not path.isdir(f"img/{today_date}"):
            mkdir(f"img/{today_date}")

        while self._running and count < self._limit:
            amount = randint(1, self._limit - count)
            print(f"Amount: {amount}")
            works, no_more = self._scrape(self._slug, amount)

            for work in works:
                final_title = cleanse(work.title)
                save_path = f"img/{today_date}/{final_title}.jpg"
                urlretrieve(work.image_url, save_path)
                print(f"Downloaded {count + 1}/{self._limit}")

                count += 1
                self._q.put_nowait((work, save_path))
                if count == 5:
                    sleep(5)

                if no_more:
                    break

        self._q.put_nowait(None)


def switch_desc(diff_desc: Label, descs: list[str], diff_int: int):
    """Change the artwork description based on a provided index."""

    diff_desc["text"] = descs[diff_int]


def switch_limit(quantity: Label, current_limit: int):
    """Changes the max number of Artworks to scrape."""

    new_limit = int(float(current_limit))
    quantity["text"] = f"{new_limit}".zfill(2)


def cleanse(sins):
    """Remove troublesome characters to prepare for string parsing."""

    return sub("[?:/\"'\t\n\r!@#$%&<>{}|=+`]", "", sins)


def remove_works(works: list[Guesswork]):
    """Purge list of all Guessworks for the current session."""

    for w in works:
        if not w.keep.get() and path.isfile(w.path):
            remove(w.path)
