#!/usr/bin/env python3
#
# Copyright 2020-2021 Colomban Wendling <ban@herbesfolles.org>
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

import gi
import sys
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Gst
Gst.init(sys.argv)

from gdr.combostackswitcher import ComboStackSwitcher
from gdr.player import Player

from gdr.archive import archive_open, archive_close

from daisy import package
from daisy import navigationcontrol



class PyObjectContainer(GObject.Object):
    def __init__(self, pyobj):
        self.obj = pyobj
        super().__init__()


@Gtk.Template.from_file('window.ui')
class Window(Gtk.ApplicationWindow):
    __gtype_name__ = 'GdrWindow'

    _toc_store = Gtk.Template.Child('toc-store')
    _nav_store = Gtk.Template.Child('nav-store')
    _player = Gtk.Template.Child('player')

    def __init__(self, **props):
        self._package = None

        super().__init__(**props)

    @Gtk.Template.Callback()
    def _on_toc_row_activated(self, view, path, column):
        print("TOC row %s activated" % (path))

        view.expand_row(path, False)
        model = view.get_model()
        it = model.get_iter(path)
        wrapper = model.get(it, 1)[0]
        if wrapper:
            nav_point = wrapper.obj
            print(nav_point)
            audio = next((l.audio for l in nav_point.labels), None)
            if audio:
                self._player.set_clip(audio, basedir=self._clip_basedir)
                self._player.play()

    @Gtk.Template.Callback()
    def _on_nav_row_activated(self, view, path, column):
        print("Navigation row %s activated")

        view.expand_row(path, False)
        model = view.get_model()
        it = model.get_iter(path)
        wrapper = model.get(it, 1)[0]
        print(wrapper)
        if not wrapper:
            return

        target = wrapper.obj
        print(target)
        audio = next((l.audio for l in target.labels), None)
        if audio:
            self._player.set_clip(audio, basedir=self._clip_basedir)
            self._player.play()


    def _add_nav_points(self, points, parent=None):
        for point in points:
            it = self._toc_store.append(parent, (point.labels[0].text,
                                                 PyObjectContainer(point)))
            self._add_nav_points((p for p in point), it)

    def set_package(self, opf_package):
        self._package = opf_package

        self._toc_store.clear()
        self._nav_store.clear()

        if self._package:
            nc = navigationcontrol.NavigationControl(self._package.manifest())
            self._clip_basedir = nc.basedir()

            self.set_title(nc.title())
            self._add_nav_points(nc.nav_map())

            for nav_list in nc.nav_lists():
                it = self._nav_store.append(None, (nav_list.labels[0].text,
                                                   None))
                for target in nav_list:
                    self._nav_store.append(it, (target.labels[0].text,
                                                PyObjectContainer(target)))


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.gdr.Gdr',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)

    def do_activate(self):
        for win in self.get_windows():
            if not win._package:
                break
        else:
            win = Window(application=self)
        win.present()

    def do_open(self, files, n_files, hint=None):
        for f in files:
            is_archive = False
            file_type = f.query_file_type(Gio.FileQueryInfoFlags.NONE, None)
            if file_type != Gio.FileType.DIRECTORY:
                try:
                    f = archive_open(f.get_path())
                except GLib.Error as ex:
                    print('Failed top open archive: %s' % ex.message)
                    continue
                is_archive = True
                file_type = f.query_file_type(Gio.FileQueryInfoFlags.NONE, None)
            if file_type != Gio.FileType.DIRECTORY:
                print('Invalid input file %s: not a directory nor a valid '
                      'archive file' % f.get_uri())
                if is_archive:
                    archive_close(f)
                continue

            opf = f.get_child('speechgen.opf')
            if not opf.get_path():
                print('Cannot find speechgen.opf in "%s".  If this is a '
                      'remote file or an archive, make sure you have '
                      'gvfs-fuse properly set up' % f.get_uri())
                if is_archive:
                    archive_close(f)
                continue

            pkg = package.Package(opf.get_path())

            for win in self.get_windows():
                if not win._package:
                    break
            else:
                win = Window(application=self)

            win.connect('destroy', lambda w: archive_close(f))
            win.set_package(pkg)
            win.present()


if __name__ == '__main__':
    app = Application()
    app.run(sys.argv)
