#!/usr/env/python3

import tkinter
from tkinter import ttk

class Adder(ttk.Frame):
	def __init__(self, parent, *arg, **kwargs):
		ttk.Frame.__init__(self, parent, *arg, **kwargs)
		self.root = parent
		self.init_gui()
	
	def init_gui(self):
		self.root.title('My first tkinter')

if __name__ == '__main__':
	root = tkinter.Tk()
	Adder(root)
	root.mainloop()
