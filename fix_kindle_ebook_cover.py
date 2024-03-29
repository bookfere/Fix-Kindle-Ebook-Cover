#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse

from FixCover import FixCover


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=FixCover.description,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'path', metavar='N', nargs='*', default=[],
        help='Kindle root directories (optional)',
    )
    parser.add_argument(
        '-a', '--action', dest='action',
        default='fix', choices=['fix', 'clean'],
        help='Specify an action to process ebook cover (default: fix)',
    )
    parser.add_argument(
        '-d', '--db', dest='database',
        default=None, help='Specify a sqlite3 database file.',
    )

    args = parser.parse_args()

    fix_cover = FixCover(logger=print, db=args.database)
    fix_cover.handle(action=args.action, roots=args.path)
