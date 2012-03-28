from flotype.bridge import Bridge
from flotype import tcp as net

from connection_dummy import ConnectionDummy
import unittest
 
class TestTcp(unittest.TestCase):
  def test_receive_data(self):
    dummy = ConnectionDummy()
    # ConnectionDummy is inadequate for net.Tcp
    tcp = net.Tcp(dummy)
    
    messages = ['abc', 'efghij', 'klmnop', 'rs', 't', 'uvwxyz']
    messages_packed = map(lambda arg: struct.pack('>I', len(arg)) + arg, messages)
    message = ''.join(messages_packed)
    
    messages_packed.map(lambda arg: tcp.receive_data(arg))
    
    self.assertTrue(dummy.onopened)
    self.assertEqual(messages, dummy.messages)

    for x in range(5):
      dummy.messages = []
      message = ''.join(messages_packed)
      pieces = rand(len(message)) + 1
      each_piece = len(message) // pieces
      while len(message) > 0:
        if len(message) > each_piece:
          tcp.receive_data(message[0::each_piece])
          message = message[each_piece::]
        else:
          tcp.receive_data(message)
          message = []
      self.assertEqual(messages, dummy.messages)
