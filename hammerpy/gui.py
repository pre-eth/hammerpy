from dataclasses import dataclass
from PIL import ImageTk
from queue import Queue
from threading import Thread

from tkinter import StringVar, IntVar, Canvas
from tkinter.ttk import Frame, Label, Style, Scale, Button, Radiobutton, Entry

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
  def keep(self, value: int):
    self._keep.set(value)

  @property
  def guess(self):
    return self._guess

  @guess.setter
  def guess(self, value: int):
    self._guess = value

class HammerPy(Frame):
  def __init__(self, root, width, height, bg, *args, **kwargs):
    Frame.__init__(self, root, *args, **kwargs)

    # Core vars
    self.width = width
    self.height = height
    self._background = bg
    self._success_color = "#00d176"
    self._failure_color = "#ed214a"
    self.works = []
    self._artwork_limit = 10
    self._descriptions = [
      "Easy - the price you guess has to be within +/- 25% of the actual price\n",
      "Medium - the price you guess has to be within +/- 15% of the actual price\n",
      "Hard - the price you guess has to be within +/- 5% of the actual price\n"
    ]

    self._logo = ImageTk.PhotoImage(file="img/hammer_py.png")

    self.difficulty = IntVar()
    self.difficulty.set(2)

    self._limit = IntVar()
    self._limit.set(1)

    # Initialize all styles
    self.frame_style = self.font_style = self.radio_style = self.submit_style = self.entry_style = Style()

    # On macOS, a default gray background appears for non-Canvas/Frame elements unless
    # this line is added. I don't really know why, but oh well. Fix obtained from
    # https://stackoverflow.com/a/50410938
    self.frame_style.theme_use("default")
    
    self.frame_style.configure("HammerPy.TFrame", padding=0, width=width, background=self._background, 
                        foreground="white", font=("Helvetica", 16))

    self.font_style.configure("HammerPy.TLabel", padding=15, background=self._background, 
                        foreground="white", font=("Helvetica", 16))
  
    self.radio_style.configure("HammerPy.TRadiobutton", padding=10, background=self._background, 
                                foreground="white", font=("Helvetica", 16))
    
    self.radio_style.map("HammerPy.TRadiobutton", background=[('active', self._background)],
                          indicatorcolor=[('selected', "#ffd903"),
                                          ('pressed', "#ffd903")])

    self.submit_style.configure("HammerPy.TButton", background=self._background, padding=10,
                                foreground="white", font=("Helvetica", 16))

    self.submit_style.map("HammerPy.TButton", 
                    background=[('active', "white"),
                                ("selected", "white"),
                                ("pressed", "white")],
                    foreground=[('active', self._background),
                                ("selected", self._background),
                                ("pressed", self._background)])

    # Add main application container
    self.backdrop = Frame(root, style="HammerPy.TFrame", padding=20)
    self.backdrop.pack(expand=True)
    self.draw_main_menu()

  def draw_main_menu(self):
    for widget in self.backdrop.winfo_children():
      widget.destroy()    

    # check if this a fresh start or we are returning 
    # from the conclusion of a previous game
    if self.works:
      from hammerpy.util import remove_works
      remove_works(self.works)
    
    # Add logo, introduction, and prompt
    canvas = Canvas(self.backdrop, bg=self._background, width=self._logo.width(), 
                  height=self._logo.height(), highlightthickness=0)
    canvas.create_image((0, 0), image=self._logo, anchor="nw")
    canvas.pack()

    greeting = Label(self.backdrop, 
                    style="HammerPy.TLabel",
                    font=("Helvetica Bold", 24),
                    text="HammerPy")
    greeting.pack()

    prompt = Label(self.backdrop, style="HammerPy.TLabel", 
                  text="Please configure the game to your liking below and then press Start")
    prompt.pack()
    
    # Add configuration options
    work_options = Frame(self.backdrop, style="HammerPy.TFrame")
    work_options.pack()

    quantity_label = Label(work_options, style="HammerPy.TLabel", 
                    text="Number of works to retrieve:", padding=0)

    self.quantity = Label(work_options, style="HammerPy.TLabel", text="01")
    quantity_scale = Scale(work_options, orient="horizontal", length=150, 
                          from_=1.0, to=10.0, variable=self._limit, command=self._switch_limit)

    quantity_label.grid(row=0, column=0)
    self.quantity.grid(row=0, column=1)
    quantity_scale.grid(row=0, column=2)

    diff_options = Frame(self.backdrop, style="HammerPy.TFrame")
    diff_options.pack()

    diff_level = Label(diff_options, style="HammerPy.TLabel", 
                      text="Difficulty Level:")

    radio_easy = Radiobutton(diff_options, text="Easy", variable=self.difficulty, 
                            command=self._switch_desc,
                            value=2, style="HammerPy.TRadiobutton")
    
    radio_medium = Radiobutton(diff_options, text="Medium", variable=self.difficulty, 
                              command=self._switch_desc,
                              value=1, style="HammerPy.TRadiobutton")
    
    radio_hard = Radiobutton(diff_options, text="Hard", variable=self.difficulty, 
                            command=self._switch_desc,
                            value=0, style="HammerPy.TRadiobutton")

    diff_level.grid(row=0, column=0, sticky="E")
    radio_easy.grid(row=0, column=1, sticky="W")
    radio_medium.grid(row=0, column=2, sticky="W")
    radio_hard.grid(row=0, column=3, sticky="W")

    # Add difficulty description and start game button
    self.diff_desc = Label(self.backdrop, style="HammerPy.TLabel", text=self._descriptions[0])
    self.diff_desc.pack()
    
    submit = Button(self.backdrop, command=self.collect_works, style="HammerPy.TButton", text="START") 
    submit.pack()

  def _switch_desc(self):
    from hammerpy.util import switch_desc

    switch_desc(self.diff_desc, self._descriptions, self.difficulty.get())

  def _switch_limit(self, e):
    from hammerpy.util import switch_limit

    switch_limit(self.quantity, self._limit.get())

  def draw_loading_screen(self):
    for widget in self.backdrop.winfo_children():
      widget.destroy() 

    self.action = self.stop_collecting
    self.redraw = self.draw_loading_screen

    self.loading = Label(self.backdrop, style="HammerPy.TLabel", 
                        text=f"Fetching artworks... ({len(self.works)}/{self._limit.get()})\n")
    self.loading.pack()

    self._back = Button(self.backdrop, command=self.confirm_stop, style="HammerPy.TButton", text="GO BACK")
    self._back.pack()

  def collect_works(self):
    from hammerpy.util import Scraper, update_status

    q = Queue()
    limit = self._limit.get()
    self.works = []

    self.draw_loading_screen()

    self._scraper = Scraper(q, limit, scrape_artsy)
    self._scraper.start()

    t = Thread(target=update_status, daemon=True, args=(self, q, limit))
    t.start()

  def stop_collecting(self):
    self._scraper.stop()
    self.draw_main_menu()

  def confirm_stop(self):
    for widget in self.backdrop.winfo_children():
      widget.destroy() 

    self.loading = Label(self.backdrop, style="HammerPy.TLabel", 
                        text="Return to main menu?\n")
    self.loading.pack()

    self._yes = Button(self.backdrop, command=self.action, style="HammerPy.TButton", text="YES")
    self._yes.pack(side="left", padx=25)

    self._no = Button(self.backdrop, command=self.redraw, style="HammerPy.TButton", text="NO")
    self._no.pack(side="right")
  
  def start_game(self):
    self.active_guess = 0
    self.action = self.draw_main_menu
    self.redraw = self.add_artwork

    self.add_artwork()
  
  def add_artwork(self):
    for widget in self.backdrop.winfo_children():
      widget.destroy()

    # msg only displays something on error, but it is still packed first
    self.errmsg = Label(self.backdrop, style="HammerPy.TLabel", foreground="#ff384c", 
                        text="", padding=5)
    self.errmsg.pack()

    art = self.works[self.active_guess]

    canvas = Canvas(self.backdrop, width=art.disp_width, height=art.disp_height) 
    canvas.create_image((0, 0), image=art.disp_img, anchor="nw")
    canvas.pack()

    price_entry = Frame(self.backdrop, style="HammerPy.TFrame")
    price_entry.pack(expand=True)

    directions = Label(price_entry, font=("Helvetica", 16), background=self._background,
                        foreground="white", text="Enter your guess: ")
    directions.grid(row=0, column=0, pady=25)

    self.guess_value = StringVar()
    self.guess_entry = Entry(price_entry, exportselection=0, width=16, textvariable=self.guess_value)
    self.guess_entry.grid(row=0, column=1, pady=25)

    # last item's button should say FINISH to conclude game
    button_text = "NEXT" if not self.active_guess == len(self.works) - 1 else "FINISH" 
    self.answer = Button(price_entry, command=self.log_guess, style="HammerPy.TButton", text=button_text)
    self.answer.grid(row=1, column=0, sticky='w')

    self.quit = Button(price_entry, command=self.confirm_stop, style="HammerPy.TButton", text="EXIT")
    self.quit.grid(row=1, column=1)
  
  def log_guess(self):
    print("LOGGING GUESS...")
    self.answer.state(['disabled'])
    guess = self.guess_value.get().strip()

    if guess.isnumeric():
      self.works[self.active_guess].guess = int(guess)
      self.active_guess += 1
      if self.active_guess == len(self.works):
        print("going to results")
        self.draw_results_screen()
      else:
        self.add_artwork()
    else:
      self.errmsg["text"] = "Guess must be numeric characters [0-9] only"

  def draw_results_screen(self):
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
    template_pieces = ["Artist: {}", "Title: {}", "Year: {}", "Actual price: ${}", 
                       "Acceptable range: ${}"]
    self.template = '\n\n'.join(template_pieces)
    
    # the bind call here makes sure wrap length is dynamically adjusted for longer titles
    self.results_info = Label(self.art_results, style="HammerPy.TLabel")
    self.results_info.bind('<Configure>', lambda e: self.results_info.config(wraplength=self.results_info.winfo_width()))
    self.results_info.pack()

    guessed = Label(self.art_results, style="HammerPy.TLabel", text="You guessed")
    guessed.pack()

    self.user_guess = Label(self.art_results, style="HammerPy.TLabel", padding=0,
                            font=("Helvetica Bold", 28))
    self.user_guess.pack()

    options = Frame(self.art_results, style="HammerPy.TFrame")
    options.pack()

    keep = Label(options, style="HammerPy.TLabel", 
                 text="Keep on device? ")

    self.keep_yes = Radiobutton(options, text="YES", value=1, style="HammerPy.TRadiobutton")
    self.keep_no = Radiobutton(options, text="NO", value=0, style="HammerPy.TRadiobutton")

    keep.grid(row=0, column=0, pady=10)
    self.keep_yes.grid(row=0, column=1)
    self.keep_no.grid(row=0, column=2)

    continue_options = Frame(self.art_results, style="HammerPy.TFrame")
    continue_options.pack()

    self.action = self.draw_main_menu
    self.redraw = self.draw_results_screen
    
    next_button = Button(continue_options, command=self.next_result, style="HammerPy.TButton", text="NEXT")
    next_button.grid(row=0, column=0, sticky='w', padx=20)

    exit_button = Button(continue_options, command=self.confirm_stop, style="HammerPy.TButton", text="EXIT")
    exit_button.grid(row=0, column=1, sticky='e')

    self.switch_result(0)

  def next_result(self):
    if self.active_guess + 1 < 10:
      self.switch_result(self.active_guess + 1)

  def switch_result(self, idx: int):
    if self.art_canvas.winfo_children():
      self.art_canvas.winfo_children()[0].destroy()

    self.curr_work = self.works[idx]    

    self.keep_yes["variable"] = self.keep_no["variable"] = self.curr_work.keep

    canvas = Canvas(self.art_canvas, width=self.curr_work.review_width, height=self.curr_work.review_height) 
    canvas.create_image((0, 0), image=self.curr_work.review_img, anchor="nw")
    canvas.pack()    

    # compute all values needed for template string to show user's results
    title = self.curr_work.art.title
    artist = title.split(" - ", 1)[0].strip()
    title = title.split(" - ", 1)[1].strip()
    year = title[title.rindex(' ') + 2:-1]
    title = title[:title.rindex(' ')].replace('\'', '\"')
    prices = self.curr_work.art.prices
    price = prices[0] if prices[0] == prices[1] else f"{prices[0]} - {prices[1]}"
    acceptable_range = f"{self.curr_work.lower_bound} ≤ N ≤ ${self.curr_work.upper_bound}"

    template = self.template.format(artist, title, year, price, acceptable_range)
    self.results_info["text"] = template

    # the user's guess, with color based on correctness
    self.user_guess["text"] = f"${self.curr_work.guess}"

    if self.curr_work.guess in range(self.curr_work.lower_bound, self.curr_work.upper_bound + 1):
      self.user_guess["foreground"] = self._success_color
    else:
      self.user_guess["foreground"] = self._failure_color