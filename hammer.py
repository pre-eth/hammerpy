from tkinter import Tk

from hammerpy.gui import HammerPy, remove_works

def on_close():
  remove_works(app.works)
  window.destroy()

if __name__ == "__main__":
  # setup window stuff
  width = 1080
  height = 720
  background = "#010012"
  major = 0
  minor = 5
  patch = 0

  window = Tk()
  window.title(f"HammerPy v{major}.{minor}.{patch}")
  window.geometry(f"{width}x{height}")
  window["bg"] = background

  window.protocol("WM_DELETE_WINDOW", on_close)

  app = HammerPy(window, width, height, background)

  window.mainloop()