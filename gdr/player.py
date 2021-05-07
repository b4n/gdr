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
import datetime
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gst
from gi.repository import GstPbutils

# ~ from daisy.audioclip import AudioClip


@Gtk.Template.from_file('player.ui')
class Player(Gtk.Box):
    __gtype_name__ = 'GdrPlayer'

    _slider = Gtk.Template.Child('range')
    _playpause = Gtk.Template.Child('playpause')

    @GObject.Property(type=str)
    def uri(self):
        return self._playbin.get_property('uri')

    def _set_duration(self, duration):
        self._duration = duration
        if self._duration != Gst.CLOCK_TIME_NONE:
            seconds = self._duration / Gst.SECOND
        else:
            seconds = 0
        print("updating playback duration to %ss" %
              datetime.timedelta(seconds=seconds))
        self._slider.set_range(0, seconds)

    @uri.setter
    def uri(self, uri):
        if uri == self.uri:
            return

        self._playbin.set_state(Gst.State.NULL)
        self._duration = Gst.CLOCK_TIME_NONE
        self._playbin.set_property('uri', uri)
        self._playbin.set_state(Gst.State.PAUSED)

        if self._duration == Gst.CLOCK_TIME_NONE:
            discoverer = GstPbutils.Discoverer()
            info = discoverer.discover_uri(uri)
            if info:
                self._set_duration(info.get_duration())
            else:
                print("Failed to discover media info")

    def set_clip(self, clip, basedir=None):
        path = os.path.abspath(os.path.join(basedir, clip.src))

        self.uri = "file://" + GLib.uri_escape_string(path, '/', True)
        self._slider.set_range(clip.begin, clip.end)
        print("playing %s from %s to %s" % (path, clip.begin, clip.end))
        self._playbin.seek_simple(Gst.Format.TIME,
                                  Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                  clip.begin * Gst.SECOND)

    @Gtk.Template.Callback()
    def _on_prev(self, widget):
        print("prev")
        pass

    @Gtk.Template.Callback()
    def _on_next(self, widget):
        print("next")
        pass

    @Gtk.Template.Callback()
    def _on_playpause(self, widget):
        print("playpause !")
        state = Gst.State.PLAYING if widget.get_active() else Gst.State.PAUSED
        if not self._playbin.set_state(state):
            print("Failed to set state")

    @Gtk.Template.Callback()
    def _on_seek(self, slider):
        # ~ ret, state, pending = self._playbin.get_state(Gst.CLOCK_TIME_NONE)
        # ~ if state not in (Gst.State.PLAYING, Gst.State.PAUSED):
            # ~ self._playbin.set_state(Gst.State.PAUSED)  # so we can start where we seeked

        self._playbin.seek_simple(Gst.Format.TIME,
                                  Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                  slider.get_value() * Gst.SECOND)

    def _refresh_ui(self):
        if Gst.CLOCK_TIME_NONE == self._duration:
            available, length = self._playbin.query_duration(Gst.Format.TIME)
            if available:
                self._set_duration(length)

        available, pos = self._playbin.query_position(Gst.Format.TIME)
        if available:
            self._slider.handler_block_by_func(self._on_seek)
            self._slider.set_value(pos / Gst.SECOND)
            self._slider.handler_unblock_by_func(self._on_seek)

            # meh, how am I supposed to do that?
            if pos >= self._slider.get_adjustment().get_upper() * Gst.SECOND:
                print("pausing because current pos %s is >= to end at %s" %
                      (pos / Gst.SECOND, self._slider.get_adjustment().get_upper()))
                self.pause()

        return True

    def _on_error(self, bus, msg):
        err, debug = msg.parse_error()
        print("GST ERROR: %s" % (err))
        print("debug: %s" % (debug))

        # stop playback
        self._playbin.set_state(Gst.State.READY)

    def _on_stream_end(self, bus, msg):
        print("stream end")
        self._playbin.set_state(Gst.State.PAUSED)

    def _on_state_changed(self, bus, msg):
        if msg.src != self._playbin:
            # ~ print("state changed on %s" % msg.src)
            return

        # ~ print("state changed")
        old, new, pending = msg.parse_state_changed()
        # ~ print("states: old=%s new=%s pending=%s" % (old, new, pending))
        self._refresh_ui()

        self._playpause.handler_block_by_func(self._on_playpause)
        if self._playpause.get_active() and \
                Gst.State.PLAYING not in (new, pending):
            self._playpause.set_active(False)
        elif new == Gst.State.PLAYING:
            self._playpause.set_active(True)
        self._playpause.handler_unblock_by_func(self._on_playpause)

        if self._refresh_id == 0 and new == Gst.State.PLAYING:
            self._refresh_id = GLib.timeout_add_seconds(1, self._refresh_ui)
            delta = (self._slider.get_adjustment().get_upper() - self._slider.get_adjustment().get_value()) * 1000 + 5
            self._refresh_id2 = GLib.timeout_add(delta, self._refresh_ui)
        elif self._refresh_id != 0 and Gst.State.PLAYING not in (new, pending):
            GLib.source_remove(self._refresh_id)
            GLib.source_remove(self._refresh_id2)
            self._refresh_id = 0

    def __init__(self, **props):
        self._refresh_id = 0
        self._duration = Gst.CLOCK_TIME_NONE

        self._playbin = Gst.ElementFactory.make("playbin", "playbin")

        # ~ self._playbin.flags |= (1 << 3)
        # ~ self._playbin.set_property('vis-plugin', 'wavescope')

        bus = self._playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_error)
        bus.connect("message::eos", self._on_stream_end)
        bus.connect("message::state-changed", self._on_state_changed)

        super(Gtk.Box, self).__init__(**props)

    def __del__(self):
        if self._refresh_id != 0:
            GLib.source_remove(self._refresh_id)

    def play(self):
        self._playbin.set_state(Gst.State.PLAYING)

    def pause(self):
        self._playbin.set_state(Gst.State.PAUSED)


if __name__ == '__main__':
    import sys
    import os

    Gst.init(sys.argv)

    window = Gtk.Window()
    window.connect('destroy', Gtk.main_quit)

    if len(sys.argv) > 1:
        f = sys.argv[1]
    else:
        f = "samples/speechgen0001.mp3"

    uri = "file://" + os.path.abspath(f)
    print(uri)
    player = Player(uri=uri)
    window.add(player)

    window.show_all()
    Gtk.main()
