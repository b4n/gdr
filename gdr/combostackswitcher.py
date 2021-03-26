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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk


class ComboStackSwitcher(Gtk.ComboBox):
    __gtype_name__ = 'GdrComboStackSwicther'

    @GObject.Property(type=Gtk.Stack)
    def stack(self):
        return self._stack

    def _update_model(self):
        self._model.freeze_notify()
        self._model.clear()
        has_icons = False
        for child in self._stack:
            name = self._stack.child_get_property(child, "name")
            title = self._stack.child_get_property(child, "title")
            icon_name = self._stack.child_get_property(child, "icon-name")
            has_icons = has_icons or icon_name is not None
            self._model.append((name, title or name, icon_name))
        self._renderer_icon.set_visible(has_icons)
        self._model.thaw_notify()
        if self.get_model():  # only if we're not constructing
            self.set_active_id(self._stack.get_visible_child_name())

    def _update_model_in_idle(self, container, widget):
        def idle_handler():
            self._update_model()
            return False

        GLib.idle_add(idle_handler)

    @stack.setter
    def stack(self, new_stack):
        self._model.clear()
        if self._binding:
            self._binding.unbind()
            self._binding = None
        if self._stack:
            self._stack.disconnect_by_func(sef._update_model_in_idle)
        self._stack = new_stack
        self.set_sensitive(self._stack is not None)
        if self._stack is not None:
            self._update_model()
            self._binding = self.bind_property('active-id', new_stack,
                                               'visible-child-name',
                                               GObject.BindingFlags.BIDIRECTIONAL)
            self._stack.connect_after('add', self._update_model_in_idle)
            self._stack.connect_after('remove', self._update_model_in_idle)

    def __init__(self, **props):
        self._stack = None
        self._binding = None
        self._model = Gtk.ListStore(str, str, str)

        self._renderer_icon = Gtk.CellRendererPixbuf()

        Gtk.ComboBox.__init__(self, **props)

        self.set_model(self._model)
        self.set_id_column(0)

        self.pack_start(self._renderer_icon, False)
        self.add_attribute(self._renderer_icon, 'icon-name', 2)

        renderer = Gtk.CellRendererText()
        self.pack_start(renderer, True)
        self.add_attribute(renderer, 'text', 1)



if __name__ == '__main__':
    window = Gtk.Window()
    window.connect('destroy', Gtk.main_quit)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    window.add(box)

    def add_child(stack, child, name, title=None, icon=None):
        stack.add_titled(child, name=name, title=title)
        stack.child_set_property(child, 'icon-name', icon or "")

    def add_child_sourcefunc(stack):
        print("new page")
        widget = Gtk.Label(label="New page", visible=True)
        add_child(stack, widget, "el3", "Some page", "gtk-quit")
        # ~ stack.set_visible_child(widget)
        return False

    stack = Gtk.Stack()
    add_child(stack, Gtk.Label(label="Page 1"), "el1", "First element")
    add_child(stack, Gtk.Label(label="Page 2"), "el2", "Second element", "media-playback-start")

    GLib.timeout_add_seconds(2, add_child_sourcefunc, stack)

    switcher = ComboStackSwitcher(stack=stack)
    box.pack_start(switcher, False, True, 0)

    box.pack_start(stack, True, True, 0)

    window.show_all()
    Gtk.main()
