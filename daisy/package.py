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

import os
from lxml import etree


class Package:
    def _xpath(self, path, namespaces=None, **kwargs):
        nslist = {'oeb': 'http://openebook.org/namespaces/oeb-package/1.0/'}
        if namespaces:
            nslist.update(namespaces)
        return self._tree.xpath(path, namespaces=nslist, **kwargs)

    def __init__(self, opffile, basedir=None):
        self._basedir = basedir or os.path.dirname(opffile)
        self._tree = etree.parse(opffile)
        # ~ print(etree.tostring(self._tree,
                             # ~ pretty_print=True, encoding='unicode'))
        self._id = self._xpath('oeb:package/@unique-identifier')
        self._check_manifest()

    def _check_manifest(self):
        items = self._xpath('/oeb:package/oeb:manifest/oeb:item')
        for item in items:
            item_path = os.path.join(self._basedir,
                                     item.get('href', 'MISSING'))
            assert os.path.exists(item_path)

    def manifest(self):
        return os.path.join(self._basedir,
            self._xpath('/oeb:package/oeb:manifest/oeb:item[@id="ncx"]/@href')[0])

    def resource(self):
        return os.path.join(self._basedir,
            self._xpath('/oeb:package/oeb:manifest/oeb:item[@id="resource"]/@href')[0])

    def spine(self):
        return [
            os.path.join(self._basedir, self._xpath(
                '/oeb:package/oeb:manifest/oeb:item[@id="%s"]/@href' % idref
                )[0])
            for idref in self._xpath(
                '/oeb:package/oeb:spine/oeb:itemref/@idref')
        ]
