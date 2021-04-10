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

import os
import re
import urllib
import pickle
import requests

import BeautifulSoup


CHATURBATE_URL = "https://chaturbate.com"

THUMB_BASE_URL = "https://roomimg.stream.highwebmedia.com/ri"

M3U8_PATTERN = r"(http.*?://.*?.stream.highwebmedia.com.*?m3u8)"

STREAM_PATTERN = r'EXT-X-STREAM-INF[\s\S]*?"FPS:(.*?)"[\s\S]*?RESOLUTION=(.*?)\n(chunk.*?.m3u8)'

class Chaturbate:
    """
    Parse chaturbate pages
    """
    def __init__(self, username='', password='', data_path=''):
        self._username = username
        self._password = password
        self._data_path = data_path
        self._req = requests.Session()
        self._csrftoken = self._req.cookies
        self._csrfmiddlewaretoken = ''
        self._load_cookie()


    def _save_cookie(self):
        with open(self._data_path + 'cookiejar', 'wb') as _file:
            pickle.dump(self._req.cookies, _file)
            _file.close()
        with open(self._data_path + 'csrftoken', 'wb') as _file:
            pickle.dump(self._csrftoken, _file)
            _file.close()
        with open(self._data_path + 'csrfmiddlewaretoken', 'wt') as _file:
            _file.write(str(self._csrfmiddlewaretoken))
            _file.close()


    def _load_cookie(self):
        if os.path.exists(self._data_path + 'cookiejar'):
            with open(self._data_path + 'cookiejar', 'rb') as _file:
                self._req.cookies.update(pickle.load(_file))
                _file.close()
        if os.path.exists(self._data_path + 'csrftoken'):
            with open(self._data_path + 'csrftoken', 'rb') as _file:
                self._csrftoken.update(pickle.load(_file))
                _file.close()
        if os.path.exists(self._data_path + 'csrfmiddlewaretoken'):
            with open(self._data_path + 'csrfmiddlewaretoken', 'rt') as _file:
                self._csrfmiddlewaretoken = _file.read()
                _file.close()


    def get_tags(self, category, page=1):
        """
        Get tags by the provided params.
        :param: category: str
        :param: page: int
        :return: list of tags
        """
        url = "%s/tags/%s/?page=%d" % (CHATURBATE_URL, category, page)
        req = self._req.get(url)

        parser = BeautifulSoup.BeautifulSoup(req.text)

        tags = []
        tag_rows = parser.findAll('div', {'class': 'tag_row'})
        for tag_row in tag_rows:
            tag = {}
            tag['name'] = tag_row.find('span', {'class': 'tag'}).a['title']
            tag['rooms'] = tag_row.find('span', {'class': 'rooms'}).text
            tags.append(tag)

        next_page = parser.find('a', {'class': 'next endless_page_link'})
        if not next_page:
            tag = {}
            tag['name'] = None
            tags.append(tag)

        return tags


    def get_models(self, category, tag, keyword, page=1):
        """
        Get models by the provided params.
        :param: category: str
        :param: tag: str
        :param: keyword: str
        :param: page: int
        :return: list of models
        """
        if tag:
            url = "%s/tag/%s/%s/" % (CHATURBATE_URL, tag, category)
        else:
            url = "%s/%s/" % (CHATURBATE_URL, category)

        params = {}
        if keyword:
            params['keywords'] = keyword
        if page:
            params['page'] = page

        url = '?'.join([url, urllib.urlencode(params)])

        req = self._req.get(url)

        if not self._is_logged(req.text):
            if self._login():
                req = self._req.get(url)

        parser = BeautifulSoup.BeautifulSoup(req.text)

        models = []

        class_list = parser.find('ul', {'class': 'list'})
        if not class_list:
            return models

        room_list = class_list.findAll('li', {'class': 'room_list_room'}, recursive=False)
        for room in room_list:
            if room.find('div', {'class': 'thumbnail_label_c_private_show'}):
                continue

            model = {}
            model['name'] = room.find('a')['href'].replace('/','')
            model['image'] = room.find('img')['src']

            info = 'Name: %s' % model['name']

            try:
                info = info + '\nAge: %d' % int(room.find('span', {'class': 'age'}).text)
            except ValueError:
                pass

            if room.find('span', {'class': 'genderc'}):
                info = info + '\nI am: A Couple'
            elif room.find('span', {'class': 'genderf'}):
                info = info + '\nI am: A Women'
            elif room.find('span', {'class': 'genderm'}):
                info = info + '\nI am: A Men'
            elif room.find('span', {'class': 'genders'}):
                info = info + '\nI am: A Trans'

            cams = room.find('li', {'class': 'cams'}).text.split(',')

            info = info + '\nViewers: %s\nLast Broadcast: %s\nLocation: %s\nTitle: %s' % (
                              cams[1].split(' ')[0], cams[0],
                              room.find('li', {'class': 'location'}).text,
                              room.find('ul', {'class': 'subject'}).text)

            model['info'] = info

            models.append(model)

        next_page = parser.find('a', {'class': 'next endless_page_link'})
        if not next_page:
            model = {}
            model['name'] = None
            models.append(model)

        return models


    def get_model_info(self, name):
        """
        Get model info by the name.
        :param: name: str
        :return: list of model info
        """
        url = "%s/%s/" % (CHATURBATE_URL, name)
        req = self._req.get(url)

        parser = BeautifulSoup.BeautifulSoup(req.text)

        model = {}

        model['name'] = name

        og_image = parser.find('meta', {'property': 'og:image'})
        if og_image:
            model['image'] = og_image['content']
        else:
            model['image'] = "%s/%s.jpg" % (THUMB_BASE_URL, name)

        info = ''
        attr_list = parser.findAll('div', {'class': 'attribute'})
        for attr in attr_list:
            info = info + "\n%s %s" % (attr.find('div', {'class': 'label'}).text,
                                       attr.find('div', {'class': 'data'}).text)
        og_description = parser.find('meta', {'property': 'og:description'})
        if og_description:
            info = info + '\nTitle: %s' % og_description['content']

        model['info'] = info

        playlist = ''
        scripts = parser.findAll('script')
        for script in scripts:
            if len(script.contents):
                playlists = re.findall(M3U8_PATTERN, script.contents[0])
                if playlists:
                    playlist = playlists[0].replace(r'\u002D','-')

        model['stream'] = playlist

        return model


    def get_stream(self, playlist, resolution='Auto'):
        """
        Get stream from playlist by resolution.
        :param: playlist: str
        :param: resolution: str
        :return: stream: str
        """
        if not playlist:
            return None
        regex_chunks = re.compile(STREAM_PATTERN, re.DOTALL)
        stream_base_url = re.findall(r'(.*)playlist.*', playlist)[0]
        req = requests.get(playlist)
        for _, res, chunk in regex_chunks.findall(req.text):
            resol = res.split('x')[1] + 'p'
            if resolution == resol:
                return "%s%s" % (stream_base_url, chunk)
        return playlist


    def follow_model(self, action, name):
        """
        Follow/Unfollow model by name.
        :param: action: str
        :param: name: str
        :return: current status
        """
        url = "%s/follow/%s/%s/" % (CHATURBATE_URL, action, name)

        req = self._req.post(url,
            data = {'csrfmiddlewaretoken': self._csrfmiddlewaretoken},
            cookies = self._csrftoken,
            headers = {'Referer': url})
        status = re.findall(r'"following": (.*?),', req.text)

        if not status:
            if self._login():
                req = self._req.post(url,
                    data = {'csrfmiddlewaretoken': self._csrfmiddlewaretoken},
                    cookies = self._csrftoken,
                    headers = {'Referer': url})
                status = re.findall(r'"following": (.*?),', req.text)

        if len(status) > 0:
            return status[0]
        return None


    def _is_logged(self, text):
        parser = BeautifulSoup.BeautifulSoup(text)
        return parser.find('input', {'name': 'username'}) is None


    def _login(self):
        if not self._username or not self._password:
            return False

        url = "%s/auth/login/" % (CHATURBATE_URL)
        req = self._req.get(url)

        parser = BeautifulSoup.BeautifulSoup(req.text)

        self._csrfmiddlewaretoken = parser.find('input',
                                                    {'name': 'csrfmiddlewaretoken'}).get('value')
        self._csrftoken = req.cookies

        req = self._req.post(url,
            data = {'username': self._username,
                    'password': self._password,
                    'csrfmiddlewaretoken': self._csrfmiddlewaretoken},
            cookies = self._csrftoken,
            headers = {'Referer': url})

        self._save_cookie()

        return self._is_logged(req.text)
