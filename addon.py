# -*- coding=utf8 -*-
"""
Copyright (c) 2021 WerWolf <mail4werwolf@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import sys
import urllib
import urlparse

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

from resources.lib.chaturbate import Chaturbate
from resources.lib.history    import SearchHistory


class XbmcContext(object):
    """
    Crates xbmc context
    """
    def __init__(self):
        self._url = sys.argv[0]
        self._addon = xbmcaddon.Addon(id='plugin.video.chaturbate')
        self._plugin_handle = int(sys.argv[1]) if len(sys.argv) > 1 else None
        self._plugin_id = self._addon.getAddonInfo('id')
        self._params = {}

        self._username = self._get_setting('username')
        self._password = self._get_setting('password')

        _data_path = xbmc.translatePath("special://profile/addon_data/%s/" % self._plugin_id)

        self._search_history = SearchHistory(_data_path + 'search.db')

        self._chaturbate = Chaturbate(self._username, self._password, _data_path)

        if len(sys.argv) > 2:
            params = sys.argv[2][1:]
            if len(params) > 0:
                self._params = dict(urlparse.parse_qsl(params))

        self._categories = {
            "featured": {"label": 30101, "tag":  "", "url": ""},
            "women":    {"label": 30102, "tag": "f", "url": "female-cams"},
            "men":      {"label": 30103, "tag": "m", "url": "male-cams"},
            "couples":  {"label": 30104, "tag": "c", "url": "couple-cams"},
            "trans":    {"label": 30105, "tag": "s", "url": "trans-cams"},
        }

        self._categories_extra = {
            "followed": {"label": 30106, "url": "followed-cams/online"},
            "new":      {"label": 30107, "url": "new-cams"},
            "hd":       {"label": 30108, "url": "hd-cams"},
            "euro":     {"label": 30109, "url": "euro-russian-cams"},
            "asian":    {"label": 30110, "url": "asian-cams"},
            "north":    {"label": 30111, "url": "north-american-cams"},
            "south":    {"label": 30112, "url": "south-american-cams"},
            "other":    {"label": 30113, "url": "other-region-cams"},
        }

        self._resolutions = { "0": "Auto", "1": "480p", "2": "720p", "3":"1080p" }

    def _get_setting(self, name):
        return self._addon.getSetting(name)


    def _has_auth(self):
        if not self._username or not self._password:
            xbmcgui.Dialog().ok(
                    self._addon.getLocalizedString(30201),
                    self._addon.getLocalizedString(30202))
            return False
        return True


    def run(self):
        """
        Calls other functions depending on the provided argv
        :return: None
        """
        xbmc.log("ARGV: %s" % (sys.argv), level=xbmc.LOGNOTICE)
        if not self._params:
            # If the plugin is called from Kodi UI without any parameters,
            # display the list of video categories
            self._list_categories()
            return
        if self._params['action'] == 'get_models':
            # Display the list of videos in a provided category.
            category = self._params.get('category')
            tag = self._params.get('tag')
            page = self._params.get('page')
            keyword = self._params.get('keyword')
            self._list_models(category, tag, keyword, page)
        elif self._params['action'] == 'get_tags':
            # Display the list of tags in a provided category.
            category = self._params.get('category')
            page = self._params.get('page')
            self._list_tags(category, page)
        elif self._params['action'] == 'get_searches':
            # Display the list of searches.
            self._list_searches()
        elif self._params['action'] == 'new_search':
            # Create new search.
            category = self._params.get('category')
            tag = self._params.get('tag')
            keyword = self._params.get('keyword')
            label = self._addon.getLocalizedString(30216)
            keyword = xbmcgui.Dialog().input(label, keyword, type=xbmcgui.INPUT_ALPHANUM)
            if keyword:
                self._search_history.insert(keyword, category, tag)
                self._list_models(category, tag, keyword, page=1)
        elif self._params['action'] == 'edit_search':
            # Edit search.
            category = self._params.get('category')
            tag = self._params.get('tag')
            keyword = self._params.get('keyword')
            label = self._addon.getLocalizedString(30216)
            keyword_new = xbmcgui.Dialog().input(label, keyword, type=xbmcgui.INPUT_ALPHANUM)
            if keyword_new and keyword_new != keyword:
                self._search_history.remove(keyword)
                self._search_history.insert(keyword_new, category, tag)
                xbmc.executebuiltin("Container.Refresh")
        elif self._params['action'] == 'rm_search':
            # Remove search.
            keyword = self._params.get('keyword')
            self._search_history.remove(keyword)
            xbmc.executebuiltin("Container.Refresh")
        elif self._params['action'] == 'follow':
            # Follow a model.
            self._follow_model('follow', self._params.get('model'))
        elif self._params['action'] == 'unfollow':
            # Unfollow a model.
            self._follow_model('unfollow', self._params.get('model'))
        elif self._params['action'] == 'play':
            # Play a video from a provided URL.
            self._play_stream(self._params.get('model'))


    def _list_searches(self):
        items = []

        params = {}
        params['action'] = 'new_search'

        url = '?'.join([self._url, urllib.urlencode(params)])

        label = self._addon.getLocalizedString(30213)
        item = xbmcgui.ListItem(label)
        items.append((url, item, True))

        for search in self._search_history.list():
            keyword = search['keyword']
            category = search['category']
            tag = search['tag']

            descr = ''
            params['action'] = 'get_models'
            if keyword:
                params['keyword'] = keyword
                descr = descr + "\nkeyword: " + keyword
            if category:
                params['category'] = category
                descr = descr + "\ncategory: " + category
            if tag:
                params['tag'] = tag
                descr = descr + "\ntag: " + tag
            params['page'] = 1

            url = '?'.join([self._url, urllib.urlencode(params)])

            item = xbmcgui.ListItem(keyword)
            item.setInfo('video', {'title': keyword, 'plot': descr})
            item.addContextMenuItems(
                    self._create_search_context_menu(keyword, category, tag), replaceItems=True)
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items, len(items))
        xbmcplugin.endOfDirectory(self._plugin_handle)


    def _list_categories(self):
        categories = {}
        categories.update(self._categories)
        categories.update(self._categories_extra)

        items = []

        params = {}
        params['action'] = 'get_searches'

        url = '?'.join([self._url, urllib.urlencode(params)])

        label = self._addon.getLocalizedString(30211)
        item = xbmcgui.ListItem(label)
        items.append((url, item, True))

        for category in categories:
            params['action'] = 'get_models'
            params['category'] = category
            params['page'] = 1

            url = '?'.join([self._url, urllib.urlencode(params)])

            enable = self._get_setting('category_' + category)
            rating = int(self._get_setting('rating_' + category))
            if enable.lower() == 'true':
                label = self._addon.getLocalizedString(categories[category]['label'])
                item = xbmcgui.ListItem(label)
                item.setInfo('video', {'title': label, 'genre': category, 'size': rating})
                items.append((url, item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items, len(items))
        xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_SIZE)
        xbmcplugin.endOfDirectory(self._plugin_handle)


    def _list_tags(self, category, page):
        params = {}
        params['action'] = 'get_models'
        params['category'] = category
        params['page'] = 1

        try:
            cat = self._categories[category]['tag']
        except KeyError:
            cat = ''

        tags = self._chaturbate.get_tags(cat, int(page))

        last_page = False

        items = []
        for tag in tags:
            name = tag['name']

            if name:
                rooms = tag['rooms']
                params['tag'] = name
                url = '?'.join([self._url, urllib.urlencode(params)])
                label = "%s (%s)" % (name, rooms)
                item = xbmcgui.ListItem(label)
                item.setInfo('video', {'title': label, 'genre': name})
                items.append((url, item, True))
            else:
                last_page = True

        if not last_page:
            params['action'] = 'get_tags'
            params['page'] = int(page) + 1
            url = '?'.join([self._url, urllib.urlencode(params)])
            label = self._addon.getLocalizedString(30231)
            item = xbmcgui.ListItem("%s (%d)" % (label, int(page) + 1))
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items, len(items))
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def _list_models(self, category, tag, keyword, page):
        if category == "followed" and not self._has_auth():
            return

        if not category:
            category = "featured"

        items = []

        params = {}

        if not keyword:
            params['category'] = category
            params['action'] = 'new_search'
            url = '?'.join([self._url, urllib.urlencode(params)])
            label = self._addon.getLocalizedString(30212)
            item = xbmcgui.ListItem(label)
            items.append((url, item, True))

        if tag:
            cat = self._categories[category]['tag']
            params['tag'] = tag
        else:
            categories = {}
            categories.update(self._categories)
            categories.update(self._categories_extra)
            cat = categories[category]['url']
            if not keyword and category in self._categories:
                params['action'] = 'get_tags'
                params['page'] = 1
                url = '?'.join([self._url, urllib.urlencode(params)])
                item = xbmcgui.ListItem("#tags")
                items.append((url, item, True))

        models = self._chaturbate.get_models(cat, tag, keyword, int(page))

        last_page = (len(models) == 0)

        for model in models:
            name = model['name']

            params['action'] = 'play'
            params['model'] = name

            if name:
                image = model['image']
                info = model['info']
                if model['follow']:
                    label = name + " *"
                else:
                    label = name
                url = '?'.join([self._url, urllib.urlencode(params)])
                item = xbmcgui.ListItem(label)
                item.setArt({ 'icon': image, 'thumb': image, 'fanart': image })
                item.setInfo('video', {'title': name, 'mediatype': 'video', 'plot': info})
                item.setCast([{"name": name}])
                item.addContextMenuItems(self._create_model_context_menu(name))
                items.append((url, item, False))
            else:
                last_page = True

        if not last_page:
            params['action'] = 'get_models'
            params['page'] = int(page) + 1
            url = '?'.join([self._url, urllib.urlencode(params)])
            label = self._addon.getLocalizedString(30231)
            item = xbmcgui.ListItem("%s (%d)" % (label, int(page) + 1))
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items, len(items))
        xbmcplugin.endOfDirectory(self._plugin_handle)


    def _play_stream(self, name):
        model = self._chaturbate.get_model_info(name)

        name = model['name']
        image = model['image']
        info = model['info']

        resolution = self._resolutions.get(self._get_setting('resolution'))
        if resolution == 'Auto':
            stream = model['stream']
        else:
            stream = self._chaturbate.get_stream(model['stream'], resolution)

        if stream:
            item = xbmcgui.ListItem(name, path=stream)
            item.setArt({ 'icon': image, 'thumb': image, 'fanart': image })
            item.setInfo('video', {'title': name, 'plot': info})
            if self._plugin_handle == -1:
                xbmc.Player().play(stream, item)
            else:
                xbmcplugin.setResolvedUrl(self._plugin_handle, True, listitem=item)


    def _create_model_context_menu(self, name):
        command = []
        label = self._addon.getLocalizedString(30221)
        command.append((label, self._cmd_follow_model('follow', name)))
        label = self._addon.getLocalizedString(30222)
        command.append((label, self._cmd_follow_model('unfollow', name)))
        return command


    def _cmd_follow_model(self, action, name):
        params = {}
        params['action'] = action
        params['model'] = name

        arg = '?'.join(["plugin://%s/" % self._plugin_id, urllib.urlencode(params)])

        return "XBMC.RunPlugin(%s)" % arg


    def _follow_model(self, action, name):
        if self._has_auth():
            ret = self._chaturbate.follow_model(action, name)
            xbmc.log("Model %s following status %s" % (name, ret), level=xbmc.LOGNOTICE)


    def _create_search_context_menu(self, keyword, category, tag):
        command = []
        label = self._addon.getLocalizedString(30214)
        command.append((label, self._cmd_search('edit_search', keyword, category, tag)))
        label = self._addon.getLocalizedString(30215)
        command.append((label, self._cmd_search('rm_search', keyword, category, tag)))
        return command


    def _cmd_search(self, action, keyword, category, tag):
        params = {}
        params['action'] = action
        if keyword:
            params['keyword'] = keyword
        if category:
            params['category'] = category
        if tag:
            params['tag'] = tag

        arg = '?'.join(["plugin://%s/" % self._plugin_id, urllib.urlencode(params)])

        return "XBMC.RunPlugin(%s)" % arg


if __name__ == "__main__":
    context = XbmcContext()
    context.run()
