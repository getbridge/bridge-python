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

    def test_ref_callback(self):
        dummy = bridge_dummy.BridgeDummy()
        dest = ['x', 'x', 'x']
        dest_ref = reference.Reference(dummy, dest + ["callback"]).to_dict()

        ref = reference.Reference(dummy, dest)

        # This function doesn't actually exist, so the rest of this test is pointless.
        cb = util.ref_callback(ref)

        self.assertIsInstance(util.CallbackReference, cb)
        self.assertEqual(ref.to_dict, cb.to_dict)

        args = [1,2,3]
        blk = lambda: 1
        args += blk
        cb.call(args, blk)

        self.assertEqual(args, *dummy.last_args)
        self.assertEqual(dest_ref, dummy.last_dest)

        args = [4,5,6]
        blk = lambda: 2
        args += blk
        cb.callback(args, blk)

        self.assertEqual(args, *dummy.last_args)
        self.assertEqual(dest_ref, dummy.last_dest)

