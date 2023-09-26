from tkinter import Tk

from hammerpy.gui import HammerPy

class Window():
  def __init__(self):
    self._width = 1080
    self._height = 720
    self._bg = "#010012"
    self._major = 0
    self._minor = 5
    self._patch = 1

    # setup window stuff
    self.root = Tk()
    self.root.title(f"HammerPy v{self._major}.{self._minor}.{self._patch}")
    self.root.geometry(f"{self._width}x{self._height}")
    self.root.minsize = self._width, self._height
    self.root["bg"] = self._bg

    self.app = HammerPy(self.root, self._width, self._height, self._bg)
    
    self.root.protocol("WM_DELETE_WINDOW", self.app._quit)  

    self.root.mainloop()


if __name__ == "__main__":
  window = Window()