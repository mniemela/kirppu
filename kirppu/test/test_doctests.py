import unittest
import doctest

import kirppu.util

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(kirppu.util))
    return tests
