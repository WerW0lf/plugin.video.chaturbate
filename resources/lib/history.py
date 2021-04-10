# -*- coding=utf8 -*-
"""
#******************************************************************************
# addon.py
#------------------------------------------------------------------------------
#
# Copyright (c) 2021 WerWolf <mail4werwolf@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#******************************************************************************
"""

import sqlite3

class SearchHistory:
    """
    Store search history
    """
    def __init__(self, dbpath):
        self._connect(dbpath)


    def _connect(self, dbpath):
        self._db = sqlite3.connect(dbpath)
        cur = self._db.cursor()
        try:
            cur.execute("SELECT * FROM search_history LIMIT 1;")
        except sqlite3.OperationalError:
            cur.executescript("CREATE TABLE search_history (keyword primary key, category, tag);")


    def insert(self, keyword, category, tag):
        """
        Insert item into DB
        :param: keyword: str
        :param: category: str
        :param: tag: str
        :return: None
        """
        cur = self._db.cursor()
        try:
            cur.execute("INSERT INTO search_history VALUES(?,?,?)", (keyword, category, tag))
            self._db.commit()
        except sqlite3.IntegrityError:
            pass


    def remove(self, keyword):
        """
        Remove item from DB
        :param: keyword: str
        :return: None
        """
        cur = self._db.cursor()
        cur.execute("DELETE FROM search_history WHERE keyword = ?", (keyword,))
        self._db.commit()


    def list(self):
        """
        Return items from DB
        :param: None
        :return: list of items
        """
        cur = self._db.cursor()
        cur.execute("SELECT * FROM search_history ORDER BY keyword ASC")
        results = []
        for (keyword, category, tag) in cur.fetchall():
            search = {
                'keyword': keyword,
                'category': category,
                'tag': tag
            }
            results.append(search)
        return results
