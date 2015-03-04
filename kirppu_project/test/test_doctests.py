import doctest

from kirppu import util, models


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(util))
    tests.addTests(doctest.DocTestSuite(models))
    return tests
