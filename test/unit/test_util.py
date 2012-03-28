from flotype.bridge import Bridge
from flotype import util, connection, reference
import bridge_dummy
import unittest

class TestUtil(unittest.TestCase):
    def test_generate_guid(self):
        ids = {}
        for i in range(1, 10):
            id = util.generate_guid()
            self.assertEqual(32, len(id))
            self.assertNotIn(id, ids)
            ids[id] = True

    def test_stringify_and_parse(self):
        data = {'a': 1, 'b': 'test code', 'c': {}, 'd': [1,False,None,'asdf',{'a': 1, 'b': 2}]}
        self.assertEqual(util.parse(util.stringify(data)), data)
