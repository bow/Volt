#!/usr/bin/env python

# tests for the volt.config module

import os
import unittest

from volt.config import Session


class TestConfig(unittest.TestCase):

    def setUp(self):
        test_dir = os.path.dirname(os.path.abspath(__file__))
        user_conf = os.path.join(test_dir, 'fixtures/project')
        default_conf = 'volt.test.fixtures.default'
        self.config = Session(default_conf, user_conf)

    def test_overwrite(self):
        self.assertEqual(self.config.TEST.TITLE, 'Title in user')
        self.assertEqual(self.config.TEST.DESC, 'Desc in default')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfig)
    unittest.TextTestRunner(verbosity=2).run(suite)
