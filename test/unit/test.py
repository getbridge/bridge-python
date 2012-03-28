import unittest

import test_util, test_serializer, test_tcp, test_reference

suite = unittest.TestSuite([test_util.TestUtil('test_generate_guid'),
                            test_util.TestUtil('test_stringify_and_parse'),
                            test_util.TestUtil('test_generate_guid'),
                            test_serializer.TestSerializer('test_serialize'),
                            test_serializer.TestSerializer('test_unserialize'),
                            test_reference.TestReference('test_reference')])
suite.run(unittest.TestResult())
unittest.TextTestRunner().run(suite)