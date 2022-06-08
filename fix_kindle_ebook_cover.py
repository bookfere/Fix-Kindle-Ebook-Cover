#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from FixCover import FixCover


if __name__ == "__main__":
    fix_cover = FixCover(is_cli=True)
    fix_cover.handle(sys.argv[1:])
