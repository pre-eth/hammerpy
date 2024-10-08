"""Orchestrates the GUI and handles game events and user actions."""

from math import ceil, floor
from queue import Queue, Empty
from threading import Thread
from tkinter import StringVar, IntVar, Canvas, Entry
from tkinter.ttk import (
    Frame,
    Label,
    Style,
    Scale,
    Button,
    Radiobutton,
    Combobox,
    Progressbar,
)

from PIL import Image, ImageTk

from hammerpy.artsy import scrape_artsy, Medium
from hammerpy.sothebys import scrape_sothebys, Category
from hammerpy.util import Guesswork, remove_works, Scraper, switch_desc, switch_limit


class HammerPy(Frame):
    """The main game object."""

    def __init__(self, root, width, height, bg, *args, **kwargs):
        Frame.__init__(self, root, *args, **kwargs)

        # Core vars
        self._root = root
        self.width = width
        self.height = height
        self._scraper = None
        self._background = bg
        self._success_color = "#00d176"
        self._failure_color = "#ed214a"
        self._select_color = "#ffd903"
        self.works = []
        self._artwork_limit = 10
        self._descriptions = [
            "Hard - the price you guess has to be within +/- 5% of the actual price\n",
            "Medium - the price you guess has to be within +/- 15% of the actual price\n",
            "Easy - the price you guess has to be within +/- 25% of the actual price\n",
        ]

        self._logo = ImageTk.PhotoImage(file="img/hammer_py.png")

        self.difficulty = IntVar()
        self.difficulty.set(2)

        self._limit = IntVar()
        self._limit.set(1)

        self._src = IntVar()
        self._src.set(0)

        self._slug = StringVar()

        # Initialize all styles
        frame_style = font_style = radio_style = submit_style = Style()

        # On macOS, a default gray background appears for non-Canvas/Frame elements unless
        # this line is added. I don't really know why, but oh well. Fix obtained from
        # https://stackoverflow.com/a/50410938
        frame_style.theme_use("default")

        frame_style.configure(
            "HammerPy.TFrame",
            padding=0,
            width=width,
            background=self._background,
            foreground="white",
            font=("Helvetica", 16),
        )

        font_style.configure(
            "HammerPy.TLabel",
            padding=15,
            background=self._background,
            foreground="white",
            font=("Helvetica", 16),
        )

        radio_style.configure(
            "HammerPy.TRadiobutton",
            padding=10,
            background=self._background,
            foreground="white",
            font=("Helvetica", 16),
        )

        radio_style.map(
            "HammerPy.TRadiobutton",
            background=[("active", self._background)],
            indicatorcolor=[
                ("selected", self._select_color),
                ("pressed", self._select_color),
            ],
        )

        submit_style.configure(
            "HammerPy.TButton",
            background=self._background,
            padding=10,
            foreground="white",
            font=("Helvetica", 16),
        )

        submit_style.map(
            "HammerPy.TButton",
            background=[
                ("active", "white"),
                ("selected", "white"),
                ("pressed", "white"),
            ],
            foreground=[
                ("active", self._background),
                ("selected", self._background),
                ("pressed", self._background),
            ],
        )

        # Add main application container
        self.backdrop = Frame(root, style="HammerPy.TFrame", padding=20)
        self.backdrop.pack(expand=True)

        self.draw_main_menu()

    def quit_game(self, _e=None):
        """Stop the scraper, remove unflagged downloaded works, and exit."""
        if self._scraper and self._scraper.driver:
            self._scraper.driver.quit()
        if self.works:
            remove_works(self.works)
        self._root.destroy()

    def draw_main_menu(self, _e=None):
        """Renders and lays out the main game menu (home screen)."""

        self._unbindall()
        for widget in self.backdrop.winfo_children():
            widget.destroy()

        # check if this a fresh start or we are returning
        # from the conclusion of a previous game
        if self.works:
            remove_works(self.works)

        # Add logo, introduction, and prompt
        canvas = Canvas(
            self.backdrop,
            bg=self._background,
            width=self._logo.width(),
            height=self._logo.height(),
            highlightthickness=0,
        )
        canvas.create_image((0, 0), image=self._logo, anchor="nw")
        canvas.pack()

        # Greeting
        Label(
            self.backdrop,
            style="HammerPy.TLabel",
            font=("Helvetica Bold", 24),
            text="HammerPy",
        ).pack()

        # Pack
        Label(
            self.backdrop,
            style="HammerPy.TLabel",
            text="Please configure the game to your liking below and click Start or press Return",
        ).pack()

        # Institution selection
        src_options = Frame(self.backdrop, style="HammerPy.TFrame")
        src_options.pack()

        Label(src_options, style="HammerPy.TLabel", text="Institution:").grid(
            row=0, column=0, sticky="E"
        )

        Radiobutton(
            src_options,
            text="Artsy",
            variable=self._src,
            command=self._switch_inst,
            value=0,
            style="HammerPy.TRadiobutton",
        ).grid(row=0, column=1, sticky="W")

        Radiobutton(
            src_options,
            text="Sotheby's",
            variable=self._src,
            command=self._switch_inst,
            value=1,
            style="HammerPy.TRadiobutton",
        ).grid(row=0, column=2, sticky="W")

        # Filtering selection
        filter_options = Frame(self.backdrop, style="HammerPy.TFrame")
        filter_options.pack()

        self.filter_desc = Label(
            filter_options, style="HammerPy.TLabel", text="Medium:"
        )

        self.filter_box = Combobox(
            filter_options, textvariable=self._slug, state="readonly"
        )
        self._switch_inst()
        self.filter_box.current(0)

        self.filter_desc.grid(row=0, column=0, sticky="E")
        self.filter_box.grid(row=0, column=1, sticky="W")

        # Amount of works to retrieve
        work_options = Frame(self.backdrop, style="HammerPy.TFrame")
        work_options.pack()

        Label(
            work_options,
            style="HammerPy.TLabel",
            text="Number of works to retrieve:",
            padding=0,
        ).grid(row=0, column=0)

        self.quantity = Label(
            work_options, style="HammerPy.TLabel", text=f"{self._limit.get()}".zfill(2)
        )
        self.quantity_scale = Scale(
            work_options,
            orient="horizontal",
            length=150,
            from_=1.0,
            to=10.0,
            variable=self._limit,
            command=self._switch_limit,
        )

        self.quantity.grid(row=0, column=1)
        self.quantity_scale.grid(row=0, column=2)

        diff_options = Frame(self.backdrop, style="HammerPy.TFrame")
        diff_options.pack()

        # Difficulty level
        Label(diff_options, style="HammerPy.TLabel", text="Difficulty Level:").grid(
            row=0, column=0, sticky="E"
        )

        # Easy difficulty radio button
        Radiobutton(
            diff_options,
            text="Easy",
            variable=self.difficulty,
            command=self._switch_desc,
            value=2,
            style="HammerPy.TRadiobutton",
        ).grid(row=0, column=1, sticky="W")

        # Medium difficulty radio button
        Radiobutton(
            diff_options,
            text="Medium",
            variable=self.difficulty,
            command=self._switch_desc,
            value=1,
            style="HammerPy.TRadiobutton",
        ).grid(row=0, column=2, sticky="W")

        # Hard difficulty radio button
        Radiobutton(
            diff_options,
            text="Hard",
            variable=self.difficulty,
            command=self._switch_desc,
            value=0,
            style="HammerPy.TRadiobutton",
        ).grid(row=0, column=3, sticky="W")

        # Add difficulty description and start game button
        self.diff_desc = Label(
            self.backdrop, style="HammerPy.TLabel", text=self._descriptions[2]
        )
        self.diff_desc.pack()

        Button(
            self.backdrop,
            command=self.collect_works,
            style="HammerPy.TButton",
            text="START",
        ).pack()

        # Bind events directly to backdrop so user can press whatever without clicking to get focus
        self._root.bind("q", self.quit_game)
        self._root.bind("<Return>", self.collect_works)
        self._root.bind("<Up>", self._switch_filter)
        self._root.bind("<Down>", self._switch_filter)
        self._root.bind("<Left>", self._kbd_switch_limit)
        self._root.bind("<Right>", self._kbd_switch_limit)
        self._root.bind("1", self._kbd_switch_desc)
        self._root.bind("2", self._kbd_switch_desc)
        self._root.bind("3", self._kbd_switch_desc)
        self._root.bind("a", self._switch_inst)
        self._root.bind("s", self._switch_inst)

    def _switch_inst(self, e=None):
        """Switch between Medium/Category for Artsy/Sothebys"""

        if e:
            self._src.set(e.keysym != "a")

        if not self._src.get():
            self.filter_box["values"] = [
                m.name.capitalize().replace("_", " ") for m in Medium
            ]
        else:
            self.filter_box["values"] = [c.name.capitalize() for c in Category]

        self.filter_box.current(0)

    def _switch_filter(self, e):
        """Changes the set scraping filter."""

        amount = 8 + self._src.get() * 3
        curr = self.filter_box.current()
        if e.keysym == "Down" and curr < amount - 1:
            self.filter_box.current(curr + 1)
        elif e.keysym == "Up" and curr > 0:
            self.filter_box.current(curr - 1)

    def _kbd_switch_desc(self, e):
        """For changing difficulty descriptions via keyboard nav."""

        val = abs(int(e.keysym) - 3)
        self.difficulty.set(val)
        self._switch_desc()

    def _switch_desc(self):
        """For changing the current difficulty description."""

        switch_desc(self.diff_desc, self._descriptions, self.difficulty.get())

    def _kbd_switch_limit(self, e):
        """Change the limit of Artworks to scrape via keyboard."""

        current = self.quantity_scale.get()
        if e.keysym == "Left" and current > 1.0:
            self.quantity_scale.set(current - 1.0)
        elif e.keysym == "Right" and current < 10.0:
            self.quantity_scale.set(current + 1.0)

    def _switch_limit(self, _e=None):
        """Change the limit of Artworks to scrape."""

        switch_limit(self.quantity, self._limit.get())

    def draw_loading_screen(self, _e=None):
        """Render game loading information on screen."""

        self._unbindall()
        for widget in self.backdrop.winfo_children():
            widget.destroy()

        self.action = self.stop_collecting
        self.redraw = self.draw_loading_screen

        progbar_text = Label(self.backdrop, style="HammerPy.TLabel", text="Loading...")
        progbar_text.pack(pady=10)

        self.loading = Progressbar(
            self.backdrop, length=540, value=0, maximum=self._limit.get() * 10
        )
        self.loading.pack(pady=25)

        self._root.bind("<Escape>", self.confirm_stop)

        self._back = Button(
            self.backdrop,
            command=self.confirm_stop,
            style="HammerPy.TButton",
            text="GO BACK",
        )
        self._back.pack()

    def collect_works(self, _e=None):
        """Get the"""

        self.works = []

        q = Queue()
        limit = self._limit.get()
        _src = self._src.get()

        fn = scrape_artsy if not _src else scrape_sothebys
        slug = self._slug.get().upper()

        if not _src:
            slug = Medium[slug.replace(" ", "_")].value

        self.draw_loading_screen()

        self._scraper = Scraper(q, limit, _src, slug, fn)
        self._scraper.start()

        t = Thread(target=update_status, daemon=True, args=(self, q))
        t.start()

    def stop_collecting(self, _e=None):
        """Stop the scraper."""

        self._scraper.stop()
        self.draw_main_menu()

    def confirm_stop(self, _e=None):
        """Confirm that the user wants to terminate the scraping routine early."""

        self._unbindall()
        for widget in self.backdrop.winfo_children():
            widget.destroy()

        self.loading = Label(
            self.backdrop, style="HammerPy.TLabel", text="Return to main menu?\n"
        )
        self.loading.pack()

        self._yes = Button(
            self.backdrop, command=self.action, style="HammerPy.TButton", text="YES"
        )
        self._yes.pack(side="left", padx=25)

        self._no = Button(
            self.backdrop, command=self.redraw, style="HammerPy.TButton", text="NO"
        )
        self._no.pack(side="right")

        self._root.bind("<Return>", self.action)
        self._root.bind("<Escape>", self.redraw)

    def start_game(self):
        """Begin game!"""

        # self._limit = len(self.works)
        self.active_guess = 0
        self.action = self.draw_main_menu
        self.redraw = self.add_artwork

        self.add_artwork()

    def add_artwork(self):
        """Add an artwork to the guessing block."""

        for widget in self.backdrop.winfo_children():
            widget.destroy()

        # msg only displays something on error, but it is still packed first
        self.errmsg = Label(
            self.backdrop,
            style="HammerPy.TLabel",
            foreground="#ff384c",
            text="",
            padding=5,
        )
        self.errmsg.pack()

        art = self.works[self.active_guess]

        canvas = Canvas(self.backdrop, width=art.disp_width, height=art.disp_height)
        canvas.create_image((0, 0), image=art.disp_img, anchor="nw")
        canvas.pack()

        price_entry = Frame(self.backdrop, style="HammerPy.TFrame")
        price_entry.pack(expand=True)

        directions = Label(
            price_entry,
            font=("Helvetica", 16),
            background=self._background,
            foreground="white",
            text="Enter your guess: ",
        )
        directions.grid(row=0, column=0, pady=25)

        self.guess_value = StringVar()
        self.guess_entry = Entry(
            price_entry,
            exportselection=0,
            width=10,
            textvariable=self.guess_value,
            cursor="xterm",
            background="white",
            insertbackground="black",
            foreground="black",
        )
        self.guess_entry.bind("<Return>", self.log_guess)
        self.guess_entry.focus_force()
        self.guess_entry.grid(row=0, column=1, pady=25)

        # last item's button should say FINISH to conclude game
        button_text = (
            "NEXT" if not self.active_guess == self._limit.get() - 1 else "FINISH"
        )
        self.answer = Button(
            price_entry,
            command=self.log_guess,
            style="HammerPy.TButton",
            text=button_text,
        )
        self.answer.grid(row=1, column=0, sticky="w")

        self.quit = Button(
            price_entry,
            command=self.confirm_stop,
            style="HammerPy.TButton",
            text="EXIT",
        )
        self.quit.grid(row=1, column=1)

    def log_guess(self, _e=None):
        """Record a user's price estimation."""

        self.answer.config(state="disabled")
        guess = self.guess_value.get().strip()

        if guess and guess.isnumeric():
            # Add user's guess for this Guesswork to the item itself
            self.works[self.active_guess].guess = int(guess)

            self.active_guess += 1
            if self.active_guess == len(self.works):
                self.draw_results_screen()
            else:
                self.add_artwork()
        else:
            self.errmsg["text"] = "Guess must be numeric characters [0-9] only"
            self.answer.config(state="normal")

    def draw_results_screen(self):
        """This is it! Show the user how they performed!"""

        self._unbindall()
        for widget in self.backdrop.winfo_children():
            widget.destroy()

        self.active_guess = 0

        # split screen into 2 halves:
        self.art_canvas = Frame(self.backdrop, style="HammerPy.TFrame", padding=20)
        self.art_canvas.pack(side="left")

        self.art_results = Frame(self.backdrop, style="HammerPy.TFrame", padding=20)
        self.art_results.pack(side="right")

        # instead of having multiple labels to update for all these items
        # just have one that is updated based on this template string
        template_pieces = [
            "Artist: {}",
            "Title: {}",
            "Year: {}",
            "Actual price: ${}",
            "Valid Guesses: ${} ≤ N ≤ ${}",
        ]
        self.template = "\n\n".join(template_pieces)

        # the bind call here makes sure wrap length is dynamically adjusted for longer titles
        self.results_info = Label(self.art_results, style="HammerPy.TLabel")
        self.results_info.bind(
            "<Configure>",
            lambda e: self.results_info.config(
                wraplength=self.results_info.winfo_width()
            ),
        )
        self.results_info.pack()

        guessed = Label(self.art_results, style="HammerPy.TLabel", text="You guessed")
        guessed.pack()

        self.user_guess = Label(
            self.art_results,
            style="HammerPy.TLabel",
            padding=0,
            font=("Helvetica Bold", 28),
        )
        self.user_guess.pack()

        options = Frame(self.art_results, style="HammerPy.TFrame")
        options.pack()

        keep = Label(options, style="HammerPy.TLabel", text="Keep on device? ")

        self.keep_yes = Radiobutton(
            options, text="YES", value=1, style="HammerPy.TRadiobutton"
        )
        self.keep_no = Radiobutton(
            options, text="NO", value=0, style="HammerPy.TRadiobutton"
        )

        keep.grid(row=0, column=0, pady=5)
        self.keep_yes.grid(row=0, column=1)
        self.keep_no.grid(row=0, column=2)

        continue_options = Frame(self.art_results, style="HammerPy.TFrame")
        continue_options.pack()

        self.action = self.draw_main_menu
        self.redraw = self.draw_results_screen

        self.next_button = Button(
            continue_options,
            command=self.next_result,
            style="HammerPy.TButton",
            text="NEXT",
        )
        self.next_button.grid(row=0, column=0, sticky="w", padx=20)

        exit_button = Button(
            continue_options,
            command=self.confirm_stop,
            style="HammerPy.TButton",
            text="EXIT",
        )
        exit_button.grid(row=0, column=1, sticky="e")

        self.switch_result()

    def next_result(self):
        """Move to the next result, and print info on screen."""

        if self.active_guess + 1 < self._limit.get():
            self.active_guess += 1
            self.switch_result()

    def switch_result(self):
        """Generic function for switching to a given Guesswork result."""

        if self.art_canvas.winfo_children():
            self.art_canvas.winfo_children()[0].destroy()

        self.curr_work = self.works[self.active_guess]

        self.keep_yes["variable"] = self.keep_no["variable"] = self.curr_work.keep

        canvas = Canvas(
            self.art_canvas,
            width=self.curr_work.review_width,
            height=self.curr_work.review_height,
        )
        canvas.create_image((0, 0), image=self.curr_work.review_img, anchor="nw")
        canvas.pack()

        # compute all values needed for template string to show user's results
        title = self.curr_work.art.title
        pieces = title.split(" - ", 1)
        if len(pieces) == 1:
            artist = ""
            year = ""
            title = pieces[0].strip()
        else:
            artist = pieces[0].strip()
            title = pieces[1].strip()
            year = title[title.rindex(" ") + 2 : -1]
            title = f"\"{title[1:title.rindex(' ') - 1]}\""

        prices = self.curr_work.art.prices
        price = prices[0] if prices[0] == prices[1] else f"{prices[0]} - {prices[1]}"

        if not artist:
            self.results_info["text"] = (
                self.template.replace("Artist: {}\n\n", "")
                .replace("Year: {}\n\n", "")
                .format(
                    title, price, self.curr_work.lower_bound, self.curr_work.upper_bound
                )
            )
        else:
            self.results_info["text"] = self.template.format(
                artist,
                title,
                year,
                price,
                self.curr_work.lower_bound,
                self.curr_work.upper_bound,
            )

        # the user's guess, with color based on correctness
        self.user_guess["text"] = f"${self.curr_work.guess}"

        if self.curr_work.guess in range(
            self.curr_work.lower_bound, self.curr_work.upper_bound + 1
        ):
            self.user_guess["foreground"] = self._success_color
        else:
            self.user_guess["foreground"] = self._failure_color

        if self.active_guess == self._limit.get() - 1:
            self.next_button["text"] = "FINISH"
            self.next_button["command"] = self.draw_main_menu

    def _unbindall(self):
        """Stop listening to all keyboard functions."""

        self._root.unbind("1")
        self._root.unbind("2")
        self._root.unbind("3")
        self._root.unbind("q")
        self._root.unbind("a")
        self._root.unbind("s")
        self._root.unbind("<Escape>")
        self._root.unbind("<Return>")
        self._root.unbind("<Up>")
        self._root.unbind("<Down>")
        self._root.unbind("<Left>")
        self._root.unbind("<Right>")


# separate function in separate thread from HammerPy
# because main thread must run GUI
def update_status(h: HammerPy, q: Queue):
    """Runs the scraping routine, updates user on collection status."""

    disp_height = h.height - 200
    factor = 0.05 + (0.1 * h.difficulty.get())

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
            review_height = 500.0 / (float(width) / float(height))

        keep = IntVar()
        keep.set(0)

        guess_work = Guesswork(
            work,
            save_path,
            ImageTk.PhotoImage(image=img.resize((ceil(disp_width), disp_height))),
            ImageTk.PhotoImage(image=img.resize((500, ceil(review_height)))),
            ceil(disp_width),
            disp_height,
            500,
            ceil(review_height),
            floor(work.prices[0] * (1.0 - factor)),
            floor(work.prices[-1] * (1.0 + factor)),
            keep,
        )

        h.works.append(guess_work)
        h.loading["value"] = len(h.works) * 10

    # Queue has been read in full, start the actual guessing game
    h.start_game()
