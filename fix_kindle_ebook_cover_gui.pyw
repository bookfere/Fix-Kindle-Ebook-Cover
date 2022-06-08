#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Tkinter API Reference: https://tkdocs.com/pyref/index.html

import threading
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext

from FixCover import FixCover


class Application(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master, padding=10)
        self.entryvalue = StringVar(self)
        self.grid()
        self.create_widgets()
        self.layout_widgets()
        self.fixcover = FixCover(
            False,
            self.get_logger(),
            self.get_progress()
        )

        roots = self.fixcover.get_kindle_root_automatically()
        if len(roots) > 0:
            root = roots[0]
            self.entryvalue.set(root)
            self.insert_log('A Kindle root directory was detected: %s' % root)


    def get_kindle_root(self, event=None):
        value = filedialog.askdirectory()
        if value != '':
            self.entryvalue.set(value)


    def reset_kindle_root(self, event):
        self.entryvalue.set(self.entry.get())


    def get_logger(self):
        def logger(text):
            self.insert_log(text)
            self.log.see(END)
        return logger


    def insert_log(self, text):
        self.log.insert(END, '%s\n' % text)


    def get_progress(self):
        self.progress['value'] = 0
        def progress(factor):
            if factor == 0:
                self.progress['value'] = 100
                return
            self.progress.step(100 / factor)
        return progress


    def fix_ebook_cover(self):
        self.log.delete(1.0, END)
        def fix_thread():
            self.fixcover.handle(self.entryvalue.get())
        threading.Thread(target=fix_thread).start()


    def create_widgets(self):
        self.entry = ttk.Entry(self, width=40, textvariable=self.entryvalue)
        self.entry.bind('<FocusOut>', self.reset_kindle_root)
        self.entry.bind('<Double-1>', self.get_kindle_root)
        self.choose = ttk.Button(self, text='Choose the Kindle root directory',
            command=self.get_kindle_root)
        self.fix = ttk.Button(self, text='Fix Cover',
            command=self.fix_ebook_cover)
        self.progress = ttk.Progressbar(self, length=580, mode='determinate',
            maximum=100)
        self.log = scrolledtext.ScrolledText(self)


    def layout_widgets(self):
        self.entry.grid(column=0, row=0, columnspan=2, sticky=S)
        self.choose.grid(column=0, row=1, padx=5, pady=5, sticky=NE)
        self.fix.grid(column=1, row=1, padx=5, pady=5, sticky=NW)
        self.progress.grid(column=0, row=2, columnspan=2)
        self.log.grid(column=0, row=3, pady=10, columnspan=2)


if __name__ == "__main__":
    root = Tk()
    root.resizable(width=False, height=False)

    app = Application(root)
    app.master.title('Fix Kindle Ebook Cover - %s' % FixCover.version)
    app.mainloop()
