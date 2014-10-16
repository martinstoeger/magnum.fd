#!/usr/bin/python

# Copyright 2012-2014 by the MicroMagnum Team
# Copyright 2014 by the magnum.fd Team
#
# This file is part of magnum.fd.
# magnum.fd is based heavily on MicroMagnum.
# (https://github.com/MicroMagnum/MicroMagnum)
#
# magnum.fd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# magnum.fd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with magnum.fd. If not, see <http://www.gnu.org/licenses/>.

import unittest

from magnum import create_controller


class ControllerTest(unittest.TestCase):

    def test_empty_parameters(self):
        c = create_controller(lambda: None, [])
        self.assertEqual([], c.all_params)

    def test_simple_parameters(self):
        c = create_controller(lambda x: None, [1, 3, 5])
        self.assertEqual(list(enumerate([(1,), (3,), (5,)])), c.all_params)

    def test_product_parameters(self):
        c = create_controller(lambda x, y: None, [(1, [2, 3])])
        self.assertEqual(list(enumerate([(1, 2), (1, 3)])), c.all_params)

    def test_complicated_parameters(self):
        c = create_controller(lambda x, y: None, [(1, [2, 3]), (4, 5)])
        self.assertEqual(list(enumerate([(1, 2), (1, 3), (4, 5)])), c.all_params)

if __name__ == '__main__':
    unittest.main()
