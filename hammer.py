"""Main application runner for HammerPy - entry point"""

from tkinter import Tk

from hammerpy.gui import HammerPy


class Window:
    """The game window. Runs thbe main event loop after defining some basic styles"""

    def __init__(self):
        self._width = 1080
        self._height = 720
        self._bg = "#010012"
        self.root = Tk()
        self.app = HammerPy(self.root, self._width, self._height, self._bg)

    def setup_window(self):
        """Defines style properties and some basic metadata"""

        _major = 0
        _minor = 5
        _patch = 4

        self.root.title(f"HammerPy v{_major}.{_minor}.{_patch}")
        self.root.geometry(f"{self._width}x{self._height}")
        self.root.minsize = self._width, self._height
        self.root["bg"] = self._bg

    def run_app(self):
        """Launches the application"""

        self.root.protocol("WM_DELETE_WINDOW", self.app.quit_game)
        self.root.bind("<Control_L>+q", self.app.quit_game)
        self.root.createcommand("::tk::mac::Quit", self.app.quit_game)

        self.root.mainloop()


if __name__ == "__main__":
    window = Window()
    window.setup_window()
    window.run_app()
