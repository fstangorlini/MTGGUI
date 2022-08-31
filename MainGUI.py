import queue
from tkinter import *
from tkinter.ttk import *
import queue
from MTGBoosterGeneratorGUI import MTGBoosterGeneratorGUI
from MTGCollectionsGUI import MTGCollectionsGUI
from tkinter.font import BOLD

# creates a Tk() object
master = Tk()
queue_ = queue.Queue()

master.geometry("300x170")
master.resizable(False, False)


def openBoosterGenerator():
    b = MTGBoosterGeneratorGUI(queue_)

def openCollection():
    c = MTGCollectionsGUI(queue_)
    

title = 'Magic the Gathering'
label_subtitle = Label(master, text =title, font=("Segoe UI", 16, BOLD))

label_subtitle.pack(pady = 10)
master.title(title)

# a button widget which will open a
# new window on button click
btn1 = Button(master, text ="Generate Booster", command = openBoosterGenerator)
btn1.pack(pady = 10)

btn2 = Button(master, text ="Check Collection", command = openCollection)
btn2.pack(pady = 10)

# mainloop, runs infinitely
mainloop()
