from flotype.bridge import Bridge
from flotype import util, connection, reference, serializer

from bridge_dummy import BridgeDummy
import reference_dummy
import unittest

class TestSerializer(unittest.TestCase):
    def test_serialize(self):
        dummy = BridgeDummy()
        test1 = Test1()
        test2 = Test2()
        test3 = Test3()
        test4 = lambda:1
        obj = {
            'a': {
                'b': test1
                },
            'c': 5,
            'd': True,
            'e': 'abc',
            'f': [test2, test3],
            'g': test2,
            'h': test3,
            'i': test4
            }
        ser = serializer.serialize(dummy, obj)

        self.assertTrue([test1, ['a', 'b']] in dummy.stored)
        self.assertTrue([test2, ['c']] in dummy.stored)
        self.assertTrue([test3, ['c', 'd', 'e']] in dummy.stored)

        found = False
        for x in dummy.stored:
            if x[1] == ['callback']:
                print(x[0])
                self.assertIsInstance(x[0], serializer.Callback)
                found = True
        self.assertTrue(found)

        expected_ser = {
            'a': {
                'b': "dummy"
                },
            'c': 5,
            'd': True,
            'e': 'abc',
            'f': ["dummy", "dummy"],
            'g': "dummy",
            'h': "dummy",
            'i': "dummy" }

        self.assertEqual(expected_ser, ser)
        return

    def test_unserialize(self):
        dummy = BridgeDummy()
        obj = { 'a': {'ref': ['x','x','x'], 'operations': ['a','b']},
                'b': {'i': {'ref': ['z','z','z'], 'operations': ['callback']}},
                'c': 5,
                'd': True,
                'e': 'abc',
                'f': [1, {'ref': ['y','y','y'], 'operations': ['c','d']}],
                'g': 2,
                'h': 'foo' }
        unser = serializer.unserialize(dummy, obj)

        self.assertIsInstance(unser['a'], reference.Reference)
        self.assertIsInstance(unser['f'][1], reference.Reference)

        # Is a lambda, not a callbackreference.
        # self.assertIsInstance(unser['b']['i'], CallbackReference)
        return


class Test1():
    def a(self):
        return

    def b(self):
        return

class Test2():
    def c(self):
        return

class Test3(Test2):
    def d(self):
        return
    def e(self):
        return
