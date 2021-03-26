#!/usr/bin/env python3
#
# Copyright 2020 Colomban Wendling <ban@herbesfolles.org>
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

# http://www.daisy.org/z3986/2005/Z3986-2005.html#NCX

import os
from lxml import etree
from .audioclip import AudioClip


def _xpath(node, path, namespaces=None, **kwargs):
    nslist = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
    if namespaces:
        nslist.update(namespaces)
    return node.xpath(path, namespaces=nslist, **kwargs)


class Audio(AudioClip):
    @property
    def clipBegin(self):
        return self.begin

    @property
    def clipEnd(self):
        return self.end

    def __init__(self, node):
        begin = node.get('clipBegin')
        end = node.get('clipEnd')
        src = node.get('src')
        self.id = node.get('id', None)
        self.cls = node.get('class', None)
        super().__init__(begin, end, src)

    def __str__(self):
        return f'<audio clipBegin="{self.begin}" clipEnd="{self.end}" src="{self.src}" />'


class Img:
    def __init__(self, node):
        self.id = node.get('id', None)
        self.cls = node.get('class', None)
        self.src = node.get('src')

    def __str__(self):
        return f'<img id="{self.id}" class="{self.cls}" src="{self.src}" />'


class NavLabel:
    def __init__(self, node):
        self.lang = node.get('xml:lang', None)
        self.dir = node.get('dir', None)
        # FIXME: text is optional if audio is provided
        self.text = _xpath(node, './ncx:text/text()')[0]

        nodes = _xpath(node, './ncx:audio')
        self.audio = Audio(nodes[0]) if nodes else None

        nodes = _xpath(node, './ncx:img')
        self.img = Img(nodes[0]) if nodes else None


class NavPoint(list):
    def __init__(self, node):
        self.id = node.get('id')
        self.play_order = int(node.get('playOrder'))

        self.labels = [NavLabel(l) for l in _xpath(node, './ncx:navLabel')]
        self.content = _xpath(node, './ncx:content/@src')[0]

        for child in _xpath(node, './ncx:navPoint'):
            self.append(NavPoint(child))
        self.sort(key=lambda p: p.play_order)

    def __repr__(self):
        return f'{type(self)}{{{self.id} {repr(self.labels[0].text)} {super().__repr__()}}}'


class NavMap(list):
    def __init__(self, node):
        self.id = node.get('id', None)

        # TODO: navInfo
        self.labels = [NavLabel(l) for l in _xpath(node, './ncx:navLabel')]
        for point in _xpath(node, './ncx:navPoint'):
            self.append(NavPoint(point))
        self.sort(key=lambda p: p.play_order)

    def __repr__(self):
        return f'{type(self)}{{{self.id} {repr(self.labels[0].text) if self.labels else None} {super().__repr__()}}}'


class NavTarget:
    def __init__(self, node):
        self.id = node.get('id')
        self.value = int(node.get('value', -1))
        self.cls = node.get('class', None)
        self.play_order = int(node.get('playOrder'))

        self.labels = [NavLabel(l) for l in _xpath(node, './ncx:navLabel')]
        self.content = _xpath(node, './ncx:content/@src')[0]

    def __repr__(self):
        return f'{type(self)}{{{self.id} {repr(self.labels[0].text)} {super().__repr__()}}}'


class NavList(list):
    def __init__(self, node):
        self.id = node.get('id', None)

        # TODO: navInfo
        self.labels = [NavLabel(l) for l in _xpath(node, './ncx:navLabel')]
        for target in _xpath(node, './ncx:navTarget'):
            self.append(NavTarget(target))
        self.sort(key=lambda p: p.play_order)

    def __repr__(self):
        return f'{type(self)}{{{self.id} {repr(self.labels[0].text) if self.labels else None} {super().__repr__()}}}'


class NavigationControl:
    def _xpath(self, path, node=None, namespaces=None, **kwargs):
        if node is None:
            node = self._tree
        return _xpath(node, path, namespaces=namespaces, **kwargs)

    def __init__(self, ncxfile, basedir=None):
        self._basedir = basedir or os.path.dirname(ncxfile)
        self._tree = etree.parse(ncxfile)
        # ~ print(etree.tostring(self._tree,
                             # ~ pretty_print=True, encoding='unicode'))

    def basedir(self):
        return self._basedir

    def title(self):
        return self._xpath('/ncx:ncx/ncx:docTitle/ncx:text/text()')[0]

    def author(self):
        return self._xpath('/ncx:ncx/ncx:docAuthor/ncx:text/text()')[0]

    def nav_map(self):
        return NavMap(self._xpath('/ncx:ncx/ncx:navMap')[0])

    def nav_lists(self):
        return [NavList(l) for l in self._xpath('/ncx:ncx/ncx:navList')]
