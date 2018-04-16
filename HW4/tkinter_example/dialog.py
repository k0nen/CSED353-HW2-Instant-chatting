#!/usr/env/python3
import tkinter

root = tkinter.Tk()

lbl = tkinter.Label(root, text="name")
lbl.grid(row=0,column=0)

txt = tkinter.Entry(root)
txt.grid(row=0,column=1)

btn = tkinter.Button(root, text="OK")
btn.grid(row=0,column=1)

root.mainloop()
