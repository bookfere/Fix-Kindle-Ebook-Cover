# Fix-Kindle-Ebook-Cover

This is a Python script to fix damaged ebook cover like below in kindle.

![](screenshots/damaged-kindle-ebook-covers.png)

Detail: [https://bookfere.com/post/986.html](https://bookfere.com/post/986.html)

## Installation

Clone or download this repository:

```console
$ git clone https://github.com/bookfere/Fix-Kindle-Ebook-Cover.git
```

You also need to [install Python](https://www.python.org/downloads/) (Required version __>= 3.5__).

## Usage

__GUI version:__

Double click __fix_kindle_ebook_thumbnails.pyw__. and choose a Kindle root directory, then click "Fix Cover" button.

![](screenshots/fix-kindle-ebook-cover-gui.png)

__CLI version:__

Run the script __fix_kindle_ebook_thumbnails.py__ on terminal with zero, one or more Kindle root directories.

```console
$ python3 fix_kindle_ebook_cover.py
$ python3 fix_kindle_ebook_cover.py /path/to/kindle
$ python3 fix_kindle_ebook_cover.py /path/to/kindle1 /path/to/kindle2
```

![](screenshots/fix-kindle-ebook-cover-cli.png)

## Technical details

Most of the heavy lifting is done by other people's code, which is included in this repo:

* Base code is from [Alex Chan](https://github.com/alexwlchan/get-mobi-cover-image). Used under GPL-3.
* `File.py` is from [KindleButler](https://github.com/AcidWeb/KindleButler) by **Paweł Jastrzębski**. Used under GPL-3.
* `DualMetaFix.py` by **K. Hendricks**. Used under GPL-3.
* `KindleUnpack.py` by **M. Hannum, P. Durrant, K. Hendricks, S. Siebert, fandrieu, DiapDealer, nickredding**. Used under GPL-3.

## License

GPL v3.
