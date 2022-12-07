# Tkinter API Reference: https://tkdocs.com/pyref/index.html

import sys
import threading
from tkinter import (
    Tk, StringVar, ttk, filedialog, scrolledtext, DISABLED, NORMAL, END, E, W
)

from FixCover import FixCover


class Application(ttk.Frame):
    def __init__(self):
        root = Tk()
        super().__init__(root, padding=10)

        self.entryvalue = StringVar(self)

        self.grid()
        self.create_widgets()
        self.layout_widgets()
        self.bind_action()

        self.fixcover = FixCover(
            logger=self.get_logger,
            progress=self.get_progress,
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

    def get_logger(self, text):
        self.insert_log(text)
        self.log.see(END)

    def insert_log(self, text):
        self.log.insert(END, '%s\n' % text)

    def get_progress(self, factor):
        if factor == 0:
            self.progress['value'] = 100
            return
        self.progress.step(float(str(100 / factor)[:3]))

    def handle_ebook_cover(self, action='fix'):
        self.log.delete(1.0, END)
        self.progress['value'] = 0
        self.choose['state'] = DISABLED
        self.fixcover.handle(
            action=action,
            roots=self.entryvalue.get(),
        )
        self.choose['state'] = NORMAL

    def fire_thread(self):
        threading.Thread(
            target=self.handle_ebook_cover,
            kwargs={'action': 'fix'},
            daemon=True,
        ).start()

    def create_widgets(self):
        self.control = ttk.Frame(self)
        self.entry = ttk.Entry(
            self.control, textvariable=self.entryvalue
        )
        self.choose = ttk.Button(
            self.control, text='Choose', command=self.get_kindle_root
        )
        self.recover = ttk.Button(
            self.control, text='Recover', command=self.fire_thread
        )
        self.progress = ttk.Progressbar(
            self, length=580, mode='determinate', maximum=100
        )
        self.log = scrolledtext.ScrolledText(self)

    def layout_widgets(self):
        self.control.grid(column=0, row=0, sticky=W+E)
        self.entry.grid(column=0, row=0, sticky=W+E)
        self.choose.grid(column=1, row=0, sticky=E)
        self.recover.grid(column=2, row=0, sticky=E)
        self.progress.grid(column=0, row=1, pady=10)
        self.log.grid(column=0, row=2)

        self.control.columnconfigure(0, weight=30)
        self.control.columnconfigure(1, weight=1)
        self.control.columnconfigure(2, weight=1)

    def bind_action(self):
        self.entry.bind('<FocusOut>', lambda e: self.reset_kindle_root())
        self.entry.bind('<Double-1>', lambda e: self.get_kindle_root())


def main():
    app = Application()
    app.master.withdraw()
    if sys.platform.startswith('win32'):
        app.master.iconbitmap('assets/icon.ico')
    app.master.title('Fix Kindle Ebook Cover - %s' % FixCover.version)
    app.master.update()
    app.master.resizable(width=False, height=False)
    width = app.master.winfo_width()
    height = app.master.winfo_height()
    x = round(app.master.winfo_screenwidth() / 2 - width / 2)
    y = round(app.master.winfo_screenheight() / 2 - height / 2)
    app.master.geometry('%sx%s+%s+%s' % (width, height, x, y))
    app.master.deiconify()

    app.mainloop()


if __name__ == "__main__":
    main()
