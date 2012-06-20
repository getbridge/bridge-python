from BridgePython.bridge import Bridge
from BridgePython import reference
from bridge_dummy import BridgeDummy
import unittest
 
class TestReference(unittest.TestCase):
  def test_reference(self):
      dummy = BridgeDummy()
      ref = reference.Reference(dummy, ['x', 'y', 'z'], ['a', 'b', 'c'])
      self.assertEqual(['a', 'b', 'c'], ref._operations)
      self.assertEqual({'ref': ['x', 'y', 'z'], 'operations': ['a', 'b', 'c']}, ref._to_dict())

      blk = (lambda: 1)
      ref.test(1, 2, blk)
      self.assertEqual((1,2,blk), dummy.last_args)
      self.assertEqual(['x', 'y', 'z', 'test'], dummy.last_dest['ref'])
      self.assertNotIn('operations', dummy.last_dest)
      return
