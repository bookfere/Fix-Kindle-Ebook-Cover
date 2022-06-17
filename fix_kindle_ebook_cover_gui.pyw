#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Tkinter API Reference: https://tkdocs.com/pyref/index.html

import threading
from functools import partial
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
            logger=self.get_logger(),
            progress=self.get_progress()
        )

        roots = self.fixcover.get_kindle_root_automatically()
        if len(roots) > 0:
            root = roots[0]
            self.entryvalue.set(root)
            self.insert_log('A Kindle root directory detected: %s' % root)
        else:
            self.insert_log('No Kindle root directory detected.')


    def get_kindle_root(self):
        self.entry.unbind('<Double-1>')
        self.entry.bind('<Double-1>', lambda e: self.prevent_dbclick_twice())

        value = filedialog.askdirectory()
        if value != '':
            self.entryvalue.set(value)


    def prevent_dbclick_twice(self):
        self.entry.unbind('<Double-1>')
        self.entry.bind('<Double-1>', lambda e: self.get_kindle_root())


    def reset_kindle_root(self):
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


    def handle_ebook_cover(self, action):
        self.log.delete(1.0, END)
        self.progress['value'] = 0
        def fix_thread():
            self.fixcover.handle(action, self.entryvalue.get())
        threading.Thread(target=fix_thread).start()


    def create_widgets(self):
        self.entry = ttk.Entry(self, width=40, textvariable=self.entryvalue)
        self.entry.bind('<FocusOut>', lambda e: self.reset_kindle_root())
        self.entry.bind('<Double-1>', lambda e: self.get_kindle_root())
        self.choose = ttk.Button(self, text='Choose',
            command=self.get_kindle_root)

        self.control = ttk.Frame(self)
        self.fix = ttk.Button(self.control, text='Fix Cover',
            command=lambda: self.handle_ebook_cover('fix'))
        self.clean = ttk.Button(self.control, text='Clean Cover',
            command=lambda: self.handle_ebook_cover('clean'))
        self.progress = ttk.Progressbar(self, length=580, mode='determinate',
            maximum=100)
        self.log = scrolledtext.ScrolledText(self)


    def layout_widgets(self):
        self.entry.grid(column=0, row=0, padx=5, sticky=E)
        self.choose.grid(column=1, row=0, padx=5, sticky=W)
        self.control.grid(column=0, row=1, columnspan=2)
        self.fix.grid(column=0, row=1, padx=5, pady=5, sticky=E)
        self.clean.grid(column=1, row=1, padx=5, pady=5, sticky=W)
        self.progress.grid(column=0, row=2, columnspan=2)
        self.log.grid(column=0, row=3, pady=10, columnspan=2)


def main():
    root = Tk()
    root.resizable(width=False, height=False)

    app = Application(root)

    app.master.withdraw()
    app.master.title('Fix Kindle Ebook Cover - %s' % FixCover.version)
    app.master.update()
    width = app.master.winfo_width()
    height = app.master.winfo_height()
    x = round(app.master.winfo_screenwidth() / 2 - width / 2)
    y = round(app.master.winfo_screenheight() / 2 - height / 2)
    app.master.geometry('%sx%s+%s+%s' % (width, height, x, y))
    app.master.deiconify()

    app.mainloop()


if __name__ == "__main__":
    main()
