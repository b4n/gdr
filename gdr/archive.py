#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Colomban Wendling <ban@herbesfolles.org>
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

""" A poor man's archive opener based on GIO.

    archive_open() opens a supported archive and returns a GFile that
    represents its content.  If gvfs-fuse is available, it will have a local
    path as well, otherwise it will be readable through regular GIO calls only.

    archive_close() cleans up when the archive file is not needed anymore.
    After this call neither GIO nor native paths operations are possible.

    This module is problematic in the sense it relies on GIO archive mounts,
    which can be unmounted by anybody, not only the caller.  This means that
    there is no guarantee somebody won't just close the archive on the caller.
    Doing so would lead all operations to fail on the caller, just as if the
    file disappeared. """

from gi.repository import GLib
from gi.repository import Gio


__all__ = ['archive_open', 'archive_close']


def synchronize_async(async_func, finish_func):
    """ Makes a GIO async function synchronous by running a main loop to wait
        for its result.  The way this is implemented could potentially lead to
        any GLib callback be run during its operation. """

    def wrapper(obj, *args, **kwargs):
        l = GLib.MainLoop()
        ex = None
        ret = None

        def on_finish(f, res):
            nonlocal ex
            nonlocal ret

            try:
                ret = finish_func(obj, res)
            except Exception as e:
                ex = e
            finally:
                l.quit()

        async_func(obj, *args, **kwargs, callback=on_finish)
        l.run()
        if ex is not None:
            raise ex
        return ret

    return wrapper


def archive_open(path):
    """ Opens the archive @path as a GFile representing it as a directory.
    @path must be a local path (for the moment). """

    # This is crazy, but it's the only way to get it working:
    # 1. get a URI with special characters escaped.  This makes sense.
    # 2. escape that result, so it can be part of the archive:// URI.  More tricky,
    #    but still makes some sense.
    # 3. escape the URI a *3rd* time, getting e.g. "/" to %253A.  Things that got
    #    escaped in step 1 are then escaped 3 times (e.g. "é" becomes %2525A9).
    #    GOD WHY!??
    # 4. make all this an archive:// URI
    uri = GLib.filename_to_uri(path)
    for i in range(2):  # WTF, seriously!??
        uri = GLib.uri_escape_string(uri, None, False)
    uri = 'archive://' + uri
    print(uri)

    zf = Gio.File.new_for_uri(uri)

    zf._was_already_mounted = False
    try:
        func = synchronize_async(type(zf).mount_enclosing_volume,
                                 type(zf).mount_enclosing_volume_finish)
        func(zf, Gio.MountMountFlags.NONE, None, None)
    except GLib.Error as ex:
        if ex.matches(GLib.quark_from_string('g-io-error-quark'),
                      Gio.IOErrorEnum.ALREADY_MOUNTED):
            zf._was_already_mounted = True
        else:
            raise

    return zf


def archive_close(zf):
    """ cleans up after @zf """
    if not zf._was_already_mounted:
        mount = zf.find_enclosing_mount(None)
        func = synchronize_async(type(mount).unmount_with_operation,
                                 type(mount).unmount_with_operation_finish)
        return func(mount, Gio.MountUnmountFlags.NONE, None, None)
    return True


# basic test
if __name__ == '__main__':
    from sys import argv

    for arg in argv[1:]:
        zf = archive_open(Gio.File.new_for_commandline_arg(arg).get_path())
        print('Archive members:')
        for child_info in zf.enumerate_children(Gio.FILE_ATTRIBUTE_STANDARD_NAME,
                                                Gio.FileQueryInfoFlags.NONE,
                                                None):
            name = child_info.get_name()
            print('- Name:', name)
            child = zf.get_child(name)
            print('  URI:', child.get_uri())
            print('  Local path:', child.get_path())
        archive_close(zf)
