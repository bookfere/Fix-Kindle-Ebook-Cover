import os
import re
import sys
import time
import glob
import string
import sqlite3
from pathlib import Path

from File import MOBIFile


class FixCover:
    name = 'Fix Kindle Ebook Cover'
    version = '1.2'
    feedback = 'https://bookfere.com/post/994.html'
    description = '%s - v%s\nA tool to fix damaged Kindle ebook covers.\n\
Feedback: %s' % (name, version, feedback)

    def __init__(self, logger=None, progress=None, db=None):
        self.logger = logger
        self.progress = progress

        self.guessed_asins = []

        # Only for KUAL extention
        self.db_access = False
        db_path = db if db is not None else '/var/local/cc.db'
        if (os.path.exists(db_path)):
            self.db_access = True
            self.db_connection = sqlite3.connect(
                db_path,
                check_same_thread=False
            )
            self.db_cursor = self.db_connection.cursor()

        self.log('Time: %s' % time.strftime('%Y-%m-%d %H:%M:%S'))
        self.log(self.description, True)

    def log(self, text, sep=False):
        if self.logger is not None:
            divider = '-------------------------------------------'
            text = '%s\n%s\n%s' % (divider, text, divider) \
                if sep is True else text
            self.logger(text)

    def print_progress(self, factor):
        if self.progress is not None:
            self.progress(factor)

    def get_filepath_list(self, path):
        return glob.glob('%s%s**' % (path, os.sep), recursive=True)

    def get_ebook_thumbnails_via_path(self, path):
        thumbnails = dict()
        for thumbnail in self.get_filepath_list(path):
            asin = re.match(
                rf'.*{re.escape(os.sep)}thumbnail_(.+?)[_\.].+',
                thumbnail
            )
            if asin is not None:
                thumbnails[asin.group(1)] = thumbnail
        return thumbnails

    def get_ebook_thumbnails_via_db(self):
        # self.db_cursor.row_factory = lambda cursor, row: row[0]
        thumbnails = self.db_cursor.execute(' \
            SELECT p_thumbnail FROM Entries \
            WHERE p_thumbnail IS NOT NULL \
            AND p_location IS NOT NULL')
        return [row[0] for row in thumbnails.fetchall()]

    def is_damaged_thumbnail(self, path):
        try:
            return os.path.getsize(path) < 2000
        except Exception:
            return False

    def get_damaged_thumbnails(self, path):
        thumbnails = self.get_ebook_thumbnails_via_path(path)
        for thumbnail in thumbnails.copy():
            thumbnail_path = thumbnails[thumbnail]
            if not self.is_damaged_thumbnail(thumbnail_path):
                del thumbnails[thumbnail]
        return thumbnails

    def is_valid_ebook_file(self, filename):
        for ext in ['.mobi', '.azw', '.azw3', 'azw4']:
            if filename.endswith(ext):
                return True
        return False

    def get_ebook_list_via_path(self, path):
        ebook_list = []
        for filename in self.get_filepath_list(path):
            self.get_ebook_asisn_from_filename(filename)
            if not self.is_valid_ebook_file(filename):
                continue
            ebook_list.append(filename)
        return ebook_list

    def get_ebook_asisn_from_filename(self, filename):
        asin = re.search(
            r'_([\w-]*)\.(?:kfx|azw\d{0,1}|prc|[mp]obi)$',
            filename
        )
        if asin is not None:
            self.guessed_asins.append(asin.group(1))

    def get_ebook_list_via_db(self):
        ebook_list = self.db_cursor.execute(" \
            SELECT p_uuid, p_location, p_thumbnail, p_cdeType FROM Entries \
            WHERE p_cdeType IN ('PDOC', 'EBOK') \
            AND p_location IS NOT NULL")
        return ebook_list.fetchall()

    def store_ebook_thumbnail(self, path, data):
        with open(path, 'wb') as file:
            file.write(data)

    def get_ebook_metadata(self, path):
        asin = cdetype = cover = None

        try:
            mobi_file = MOBIFile(path)
            asin = mobi_file.get_metadata('ASIN')
            cdetype = mobi_file.get_metadata('Document Type')
            cover = mobi_file.get_cover_image()
        except Exception:
            pass

        return (asin, cdetype, cover)

    def get_thumbnail_name(self, asin, cdetype):
        return 'thumbnail_%s_%s_portrait.jpg' % (asin, cdetype)

    def fix_via_db(self, thumbnails_path):
        for row in self.get_ebook_list_via_db():
            p_uuid, p_location, p_thumbnail, p_cde = row
            if not os.path.exists(p_location):
                continue

            asin, cde, cover = self.get_ebook_metadata(p_location)

            if p_location.endswith('KUAL.kual'):
                cover = Path(
                    os.path.join(os.path.dirname(__file__), 'kual.jpg')
                ).read_bytes()
            elif not self.is_valid_ebook_file(p_location):
                continue
            elif cover is None:
                self.failure_jobs['ebook_errors'].append(
                    '%s\n  └─[%s] %s' %
                    ('No cover was found.', p_cde, Path(p_location).name)
                )
                continue

            if p_thumbnail is None and p_cde in ('EBOK', 'PDOC'):
                asin = asin if asin is not None else p_uuid
                cde = cde if cde is not None else p_cde
                thumbnail_path = os.path.join(
                    thumbnails_path,
                    self.get_thumbnail_name(asin, cde)
                )
                self.store_ebook_thumbnail(thumbnail_path, cover)
                self.db_cursor.execute('UPDATE Entries SET p_thumbnail = ? \
                    WHERE p_location = ?', (thumbnail_path, p_location))
                self.log(
                    '✓ Generated: %s\n  └─[%s] %s' %
                    (Path(thumbnail_path).name, p_cde, Path(p_location).name)
                )
            elif p_thumbnail is not None and (
                not os.path.exists(p_thumbnail)
                or self.is_damaged_thumbnail(p_thumbnail)
            ):
                self.store_ebook_thumbnail(p_thumbnail, cover)
                self.log(
                    '✓ Fixed: %s\n  └─[%s] %s' %
                    (Path(p_thumbnail).name, p_cde, Path(p_location).name)
                )

    def fix_via_path(self, thumbnails, documents_path, thumbnails_path):
        ebook_list = self.get_ebook_list_via_path(documents_path)
        for ebook in ebook_list:
            self.print_progress(len(ebook_list))

            asin, cdetype, cover = self.get_ebook_metadata(ebook)
            ebook = Path(ebook)

            if cover is None:
                self.failure_jobs['ebook_errors'].append(
                    '%s\n  └─[%s] %s' %
                    ('No cover was found.', cdetype, ebook.name)
                )
                continue

            if cdetype == 'EBOK' and asin in thumbnails.keys():
                thumbnail_path = thumbnails[asin]
                thumbnail_name = Path(thumbnail_path).name
                self.store_ebook_thumbnail(thumbnail_path, cover)
                self.log(
                    '✓ Fixed: %s\n  └─[%s] %s' %
                    (thumbnail_name, cdetype, ebook.name)
                )
                self.conquest_jobs += 1
                del thumbnails[asin]
            elif cdetype == 'EBOK' and asin is not None:
                thumbnail_name = self.get_thumbnail_name(asin, cdetype)
                thumbnail_path = os.path.join(thumbnails_path, thumbnail_name)
                if not os.path.exists(thumbnail_path):
                    self.store_ebook_thumbnail(thumbnail_path, cover)
                    self.log(
                        '✓ Generated: %s\n  └─[%s] %s' %
                        (thumbnail_name, cdetype, ebook.name)
                    )
                    self.conquest_jobs += 1

        self.failure_jobs['cover_errors'] = [
            Path(thumbnail).name for thumbnail in thumbnails.values()
        ]

        self.print_progress(0)

    def fix_ebook_thumbnails(self, documents_path, thumbnails_path):
        self.log('Checking damaged ebook covers:', True)
        thumbnails = self.get_damaged_thumbnails(thumbnails_path)

        if len(thumbnails) > 1:
            for thumbnail in thumbnails:
                self.log('- %s' % Path(thumbnail).name)
        else:
            self.log('- No damaged ebook cover detected.')

        self.log('Fixing damaged or missing ebook covers:', True)

        self.conquest_jobs = 0
        self.failure_jobs = {
            'cover_errors': [],
            'ebook_errors': [],
        }

        # Only for KUAL extention
        if self.db_access:
            self.fix_via_db(thumbnails_path)
        else:
            self.fix_via_path(thumbnails, documents_path, thumbnails_path)

        if self.failure_jobs is None:
            self.log('- No ebook cover to fix.')
            return

        if any(len(job) > 0 for job in self.failure_jobs.values()):
            if len(self.failure_jobs['cover_errors']) > 0:
                self.log('- These damaged covers have no corresponding ebook.')
                for job in self.failure_jobs['cover_errors']:
                    self.log('* %s' % job)

            if len(self.failure_jobs['ebook_errors']) > 0:
                self.log(
                    '- These ebooks have no covers.'
                )
                for job in self.failure_jobs['ebook_errors']:
                    self.log('! %s' % job)
        elif self.conquest_jobs > 0:
            self.log('✓ All ebook covers were fixed.')
        else:
            self.log('- No ebook cover need to fix.')

    def clean_orphan_thumbnails(self, documents_path, thumbnails_path):
        self.log('Analysing orphan ebook covers:', True)

        thumbnails = self.get_ebook_thumbnails_via_path(thumbnails_path)

        if self.db_access:
            thumbnails = set(thumbnails.values()) \
                - set(self.get_ebook_thumbnails_via_db())
        else:
            self.log(
                'This feature Removed due to impossible to delete the orphan'
                'thumbnails perfectly.'
            )
            return
            # ebook_list = self.get_ebook_list_via_path(documents_path)
            # for ebook in ebook_list:
            #     self.print_progress(len(ebook_list))
            #     asin, cdetype, cover = self.get_ebook_metadata(ebook)
            #     if cdetype == 'EBOK' and asin in thumbnails.keys():
            #         del thumbnails[asin]
            # for asin in self.guessed_asins:
            #     if asin in thumbnails.keys():
            #         del thumbnails[asin]
            # thumbnails = thumbnails.values()

        self.print_progress(0)

        if len(thumbnails) < 1:
            self.log('- No orphan cover detected.')
            return

        for thumbnail in thumbnails:
            thumbnail_path = Path(thumbnail)
            thumbnail_path.unlink(True)
            self.log('✓ Delete: %s' % thumbnail_path.name)

        self.log('✓ All orphan ebook covers deleted.')

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

    # fix|clean
    def handle(self, action='fix', roots=[]):
        if not sys.version_info >= (3, 5):
            self.log(
                'Rquired Python version >= 3.5\n' +
                'You can download here: https://www.python.org/downloads/'
            )
            return

        roots = [roots] if type(roots) != list else roots
        roots = self.get_kindle_root_automatically() \
            if len(roots) < 1 else roots

        if len(roots) < 1:
            self.log('You need choose a Kindle root directory first.')
            return

        for root in roots:
            if root == '':
                self.log('Kindle root directory can not be empty.')
                continue

            if not self.is_kindle_root(root):
                self.log('%s is not a kindle root directory.' % root)
                continue

            self.log('Processing Kindle device: %s' % root)

            documents_path, thumbnails_path = self.get_kindle_path(root)

            if action == 'fix':
                self.fix_ebook_thumbnails(documents_path, thumbnails_path)
            elif action == 'clean':
                self.clean_orphan_thumbnails(documents_path, thumbnails_path)
            else:
                self.log('Wrong action.')
                return

            self.log('All jobs done.', True)

    def __del__(self):
        if (self.db_access):
            self.db_connection.commit()
            self.db_connection.close()
