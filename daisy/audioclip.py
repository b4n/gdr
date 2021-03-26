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

import re
from datetime import timedelta


class AudioClip:
    def __init__(self, begin, end, src):
        def ensure_time(v):
            return self.parse_smil_time(v) if isinstance(v, str) else v

        self.begin = ensure_time(begin)
        self.end = ensure_time(end)
        self.src = src

    # FIXME: isn't there any better way to do that?
    @staticmethod
    def parse_smil_time(time):
        m = re.match(r'(?:ntp=)?(?:(?:([0-9]+):)?([0-9]+):)?([0-9]+(?:[.][0-9]+)?)', time)
        if not m:
            return None
        return int(m.group(1)) * 60 * 60 + int(m.group(2)) * 60 + float(m.group(3))

    def __repr__(self):
        return f'{type(self)}{{begin={timedelta(seconds=self.begin)} end={timedelta(seconds=self.end)} src={self.src} {super().__repr__()}}}'
