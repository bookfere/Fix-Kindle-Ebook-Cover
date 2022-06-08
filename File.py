#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Pawel Jastrzebski <pawelj@iosphe.re>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__license__ = 'GPL-3'
__copyright__ = '2014, Pawel Jastrzebski <pawelj@iosphe.re>'

import os
import random
import string
from imghdr import what
from io import BytesIO
from tempfile import gettempdir
from uuid import uuid4

import DualMetaFix
import KindleUnpack


class MOBIFile:
    def __init__(self, path):
        self.path = path
        self.section = KindleUnpack.Sectionizer(self.path)
        self.mh = [KindleUnpack.MobiHeader(self.section, 0)][0]
        self.metadata = self.mh.getmetadata()
        self.check_file()

    def check_file(self):
        if not os.path.isfile(self.path):
            raise OSError('The specified file does not exist!')
        file_extension = os.path.splitext(self.path)[1].upper()
        if file_extension not in ['.MOBI', '.AZW', '.AZW3']:
            raise OSError('The specified file is not E-Book!')
        mobi_header = open(self.path, 'rb').read(100)
        palm_header = mobi_header[0:78]
        ident = palm_header[0x3C:0x3C+8]
        if ident != b'BOOKMOBI':
            raise OSError('The specified file is not E-Book!')

    def get_metadata(self, key):
        return self.metadata[key][0].decode('utf-8') \
            if key in self.metadata.keys() else None

    def get_cover_image(self):
        coverid = int(self.metadata['CoverOffset'][0])
        beg = self.mh.firstresource
        end = self.section.num_sections
        imgnames = []
        for i in range(beg, end):
            data = self.section.load_section(i)
            tmptype = data[0:4]
            if tmptype in ["FLIS", "FCIS", "FDST", "DATP"]:
                imgnames.append(None)
                continue
            elif tmptype == "SRCS":
                imgnames.append(None)
                continue
            elif tmptype == "CMET":
                imgnames.append(None)
                continue
            elif tmptype == "FONT":
                imgnames.append(None)
                continue
            elif tmptype == "RESC":
                imgnames.append(None)
                continue
            if data == chr(0xe9) + chr(0x8e) + "\r\n":
                imgnames.append(None)
                continue
            imgtype = what(None, data)
            if imgtype is None and data[0:2] == b'\xFF\xD8':
                last = len(data)
                while data[last-1:last] == b'\x00':
                    last -= 1
                if data[last-2:last] == b'\xFF\xD9':
                    imgtype = "jpeg"
            if imgtype is None:
                imgnames.append(None)
            else:
                imgnames.append(i)
            if len(imgnames)-1 == coverid:
                return data
        raise OSError
