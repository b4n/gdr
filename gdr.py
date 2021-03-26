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

""" DAISY book reading test """

from daisy import package
from daisy import navigationcontrol

p = package.Package('samples/speechgen.opf')
print(p.spine())
print(p.manifest())
print(p.resource())

nc = navigationcontrol.NavigationControl(p.manifest())
print("title:", nc.title())
print("author:", nc.author())

def printNavPoint(point, depth=0):
    print(f'{"  " * depth}{point.labels[0].text} -> {point.content}')
    for child in point:
        printNavPoint(child, depth + 1)

print("navMap:")
for point in nc.nav_map():
    printNavPoint(point, 1)

print("navLists:")
for nav_list in nc.nav_lists():
    print(f'  {nav_list.labels[0].text}')
    for target in nav_list:
        print(f'    {target.labels[0].text} -> {target.content}')
