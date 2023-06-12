#!/usr/bin/env python
# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#
# This file is used to test reading and processing of config files
#

from __future__ import absolute_import, division, print_function, unicode_literals

import six
from shinken_test import *
from shinken.safepickle import SafeUnpickler
import pickle
import sys
import io

should_not_change = False


def fff(b):
    global should_not_change
    should_not_change = b


class SadPanda(object):
    def __reduce__(self):
        return (fff, (True,))


class TestSafePickle(ShinkenTest):

    def setUp(self):
        pass


    def launch_safe_pickle(self, buf):
        SafeUnpickler(io.BytesIO(buf)).load()


    def test_safe_pickle(self):
        global should_not_change

        print("Creating payload")
        buf = pickle.dumps(SadPanda(), 0)
        should_not_change = False
        print("Payload", buf)
        print("Now loading payload")
        pickle.loads(buf)
        print(should_not_change)
        self.assertTrue(should_not_change)

        # reset and try our fix
        should_not_change = False

        def launch_safe_pickle():
            SafeUnpickler(io.BytesIO(buf)).load()

        self.assertRaises(ValueError, launch_safe_pickle)
        print (should_not_change)
        self.assertFalse(should_not_change)


    # Thanks to security team @Dailymotion, we did have a RCE that ook like a return into libc
    # exploit: they are using the bottle._load code (that blindly __import__) so the injected
    # code will finally be executed. And as it's shinken.webui.bottle, it's ok with the
    # safe_pickle filter. Smart ^^
    def test_safe_pickle_exploit_rce(self):
        # Bottle shoult not be embedded anymore
        if not six.PY2:
            return
        try:
            import shinken.webui.bottlewebui
        except ImportError:
            return

        ###### Phase 1: can be exploited
        # Arrange
        rce_path = '/rce_exploited'
        if rce_path in sys.path:
            sys.path.remove(rce_path)

        payload = """cshinken.webui.bottlewebui
_load
(S'sys:path.append("%s")'
tR.""" % rce_path
        payload = payload.encode("utf-8")

        # Act
        print("Now loading payload")
        pickle.loads(payload)

        # Assert
        self.assertTrue(rce_path in sys.path)

        ##### Phase 2: no more exploitable by calling the good one
        # Arrange
        sys.path.remove(rce_path)

        def launch_safe_pickle():
            SafeUnpickler(io.BytesIO(payload)).load()

        # Act
        self.assertRaises(ValueError, launch_safe_pickle)

        # Assert
        self.assertTrue(rce_path not in sys.path)

    # Thanks to security team @Dailymotion, we did have a RCE that ook like a return into libc
    # exploit: they are using the bottle._load code (that blindly __import__) so the injected
    # code will finally be executed. And as it's shinken.webui.bottle, it's ok with the
    # safe_pickle filter. Smart ^^
    def test_safe_pickle_exploit_rce_can_load(self):
        ###### Phase 1: can be exploited
        # Arrange

        payload = pickle.dumps(Brok('void', {}))

        # Act
        b = SafeUnpickler(io.BytesIO(payload)).load()

        # Assert
        self.assertTrue(isinstance(b, Brok))


if __name__ == '__main__':
    unittest.main()
