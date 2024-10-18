import customtkinter as ctk
from views import MainWindow, PlotsWindow, InfoNewModel
from tkinterdnd2 import TkinterDnD
import controlls as cmd



class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

class App(Tk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")
        self.title("FinAIze")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.windows = {}
        for fr in (MainWindow, InfoNewModel):
            win_name = fr.__name__
            window = fr(self)
            self.windows[win_name] = window
            window.grid(row=0, column=0, sticky="nsew")

        
        cmd.show_window(self, "MainWindow")


if __name__ == '__main__':
    # ctk.set_appearance_mode('system')
    ctk.set_appearance_mode('dark')
    app = App()
    app.mainloop()