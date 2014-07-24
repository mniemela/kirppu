import unittest
import doctest

import kirppu.util
import kirppu.app.models

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(kirppu.util))
    tests.addTests(doctest.DocTestSuite(kirppu.app.models))
    return tests
