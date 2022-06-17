#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import glob
import imghdr
import string
import tempfile
from pathlib import Path

from File import MOBIFile


class FixCover:
    version = '1.1'
    description = 'A tool to fix damaged Kindle ebook covers.\n\
Detail: https://bookfere.com/post/986.html'


    def __init__(self, logger=None, progress=None):
        self.logger = logger
        self.progress = progress

        self.print_log('Version: %s' % self.version)
        self.print_log(self.description, True)


    def print_log(self, text, sep=False):
        if self.logger is not None:
            divider = '-------------------------------------------'
            text =  '%s\n%s\n%s' % (divider, text, divider) \
                if sep is True else text
            self.logger(text)


    def print_progress(self, factor):
        if self.progress is not None:
            self.progress(factor)


    def get_filepath_list(self, path):
        return glob.glob('%s%s**' % (path, os.sep), recursive=True)


    def get_ebook_thumbnails(self, path):
        thumbnails = dict()
        for thumbnail in self.get_filepath_list(path):
            asin = re.match(rf'.*{re.escape(os.sep)}thumbnail_(.+)_EBOK.+',
                thumbnail)
            if asin is not None:
                thumbnails[asin.group(1)] = thumbnail
        return thumbnails


    def get_damaged_thumbnails(self, path):
        thumbnails = self.get_ebook_thumbnails(path)
        for thumbnail in thumbnails.copy():
            thumbnail_path = thumbnails[thumbnail]
            if os.path.getsize(thumbnail_path) < 2000:
                self.print_log('- %s' % Path(thumbnail_path).name)
            else:
                del thumbnails[thumbnail]
        return thumbnails


    def is_valid_ebook_file(self, filename):
        for ext in ['.mobi', '.azw', '.azw3', 'azw4']:
            if filename.endswith(ext):
                return True
        return False


    def get_ebook_list(self, path):
        ebook_list = []
        for filename in self.get_filepath_list(path):
            if not self.is_valid_ebook_file(filename):
                continue
            ebook_list.append(filename)
        return ebook_list


    def store_ebook_cover(self, path, data):
        with open(path, 'wb') as file:
            file.write(data)


    def get_ebook_metadata(self, path):
        ebook_asin = None
        ebook_type = None
        ebook_cover = None

        try:
            mobi_file = MOBIFile(path)
            ebook_asin = mobi_file.get_metadata('ASIN')
            ebook_type = mobi_file.get_metadata('Document Type')
            ebook_cover = mobi_file.get_cover_image()
        except:
            pass

        return (ebook_asin, ebook_type, ebook_cover)


    def get_thumbnail_name(self, asin):
        return 'thumbnail_%s_EBOK_portrait.jpg' % asin


    def fix_ebook_thumbnails(self, documents_path, thumbnails_path):
        failure_jobs = {
            'cover_errors': [],
            'ebook_errors': [],
        }

        self.print_log('Checking damaged ebook covers:', True)
        thumbnails = self.get_damaged_thumbnails(thumbnails_path)

        if len(thumbnails) < 1:
            self.print_log('No damaged ebook cover detected.')
            return

        self.print_log('Fixing damaged ebook covers:', True)
        self.print_log('Working...')

        ebook_list = self.get_ebook_list(documents_path)
        for ebook in ebook_list:
            self.print_progress(len(ebook_list))

            ebook_asin, ebook_type, ebook_cover = self.get_ebook_metadata(ebook)

            ebook = Path(ebook)

            if ebook_type == 'EBOK' and ebook_asin in thumbnails.keys():
                thumbnail_path = thumbnails[ebook_asin]
                thumbnail_name = Path(thumbnail_path).name
                if ebook_cover is not None:
                    self.store_ebook_cover(thumbnail_path, ebook_cover)
                    self.print_log('✓ Fixed: %s\n  └─[%s] %s' % (thumbnail_name,
                        ebook_type, ebook.name))
                else:
                    failure_jobs['ebook_errors'].append('%s\n  └─[%s] %s' %
                        (ebook_type, thumbnail_name, ebook.name))
                del thumbnails[ebook_asin]
            elif ebook_type == 'EBOK' and ebook_cover is not None:
                thumbnail_name = self.get_thumbnail_name(ebook_asin)
                thumbnail_path = os.path.join(thumbnails_path, thumbnail_name)
                if not os.path.exists(thumbnail_path):
                    self.store_ebook_cover(thumbnail_path, ebook_cover)
                    self.print_log('✓ Generated: %s\n  └─[%s] %s' %
                        (thumbnail_name, ebook_type, ebook.name))
            # [BUG] Do this will make Kindle can not open ebook.
            # elif ebook_type == 'PDOC' and ebook.suffix == '.azw3' and \
            #     ebook_cover is not None:
            #     target = ebook.with_suffix('.mobi')
            #     ebook.rename(target)
            #     self.print_log(
            #         '✓ Rename %s -> %s to show cover.\n  └─[%s] %s' %
            #         (ebook.suffix, target.suffix, ebook_type, target.name)
            #     )


        failure_jobs['cover_errors'] = [Path(thumbnail).name for
            thumbnail in thumbnails.values()]

        self.print_progress(0)

        if failure_jobs is None:
            self.print_log('- No ebook cover to fix.')
            return

        if any(len(job) > 0 for job in failure_jobs.values()):
            if len(failure_jobs['cover_errors']) > 0:
                self.print_log(
                    '- These damaged covers have no corresponding ebook.'
                )
                for job in failure_jobs['cover_errors']:
                    self.print_log('* %s' % job)


            if len(failure_jobs['ebook_errors']) > 0:
                self.print_log(
                    '- The ebooks corresponding to these damaged covers have no'
                    + ' covers, you can clean them.'
                )
                for job in failure_jobs['ebook_errors']:
                    self.print_log('! %s' % job)
        else:
            self.print_log('✓ All ebook covers were fixed.')


    def clean_orphan_thumbnails(self, documents_path, thumbnails_path):
        self.print_log('Analysing orphan ebook covers:', True)
        thumbnails = self.get_ebook_thumbnails(thumbnails_path)
        ebook_list = self.get_ebook_list(documents_path)
        for ebook in ebook_list:
            self.print_progress(len(ebook_list))
            ebook_asin, ebook_type, ebook_cover = self.get_ebook_metadata(ebook)
            if ebook_type == 'EBOK' and ebook_asin in thumbnails.keys():
                del thumbnails[ebook_asin]

        self.print_progress(0)

        if len(thumbnails) < 1:
            self.print_log('- No orphan covers detected.')
            return

        for thumbnail in thumbnails.values():
            thumbnail_path = Path(thumbnail)
            thumbnail_path.unlink(True)
            self.print_log('✓ Delete: %s' % thumbnail_path.name)


        self.print_log('✓ All orphan ebook covers deleted.')


    def get_kindle_path(self, path):
        return (
            os.path.join(path, 'documents'),
            os.path.join(path, 'system', 'thumbnails')
        )


    def is_kindle_root(self, path):
        for path in self.get_kindle_path(path):
            if os.path.exists(path) is False:
                return False
        return True


    def get_kindle_root_manually(self, args):
        roots = []
        for path in args:
            path = os.path.join(path)
            if self.is_kindle_root(path):
                roots.append(path)
            else:
                message = '%s is not a kindle root directory.' % path if \
                    path != '' else 'You need choose a Kindle root directory first.'
                self.print_log(message)
        return roots


    def get_kindle_root_automatically(self):
        drives = []
        roots = []

        if sys.platform.startswith('win'):
            drives = ['%s:\\' % s.upper() for s in string.ascii_lowercase[:26]]
            drives.reverse()
        elif sys.platform.startswith('darwin'):
            drives = glob.glob('/Volumes/*')

        for drive in drives:
            path = os.path.join('%s' % drive)
            if self.is_kindle_root(path):
                roots.append(path)

        return roots


    def get_kindle_root(self, roots):
        if len(roots) > 0:
            return self.get_kindle_root_manually(roots)
        return self.get_kindle_root_automatically()


    # fix|clean
    def handle(self, action='fix', path=[]):
        if not sys.version_info >= (3, 5):
            self.print_log(
                'Rquired Python version >= 3.5\n' +
                'You can download here: https://www.python.org/downloads/'
            )
            return

        path = [path] if type(path) != list else path
        kindle_roots = self.get_kindle_root(path)

        for kindle_root in kindle_roots:
            self.print_log('Processing Kindle device: %s' % kindle_root)

            documents_path, thumbnails_path = self.get_kindle_path(kindle_root)

            if action == 'fix':
                self.fix_ebook_thumbnails(documents_path, thumbnails_path)
            elif action == 'clean':
                self.clean_orphan_thumbnails(documents_path, thumbnails_path)
            else:
                self.print_log('Wrong action.')
                return

            self.print_log('All jobs done.', True)
