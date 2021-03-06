from twisted.trial import unittest
from twisted.internet import defer

import ants
from ants.utils.testproc import ProcessTest


class VersionTest(ProcessTest, unittest.TestCase):

    command = 'version'

    @defer.inlineCallbacks
    def test_output(self):
        _, out, _ = yield self.execute([])
        self.assertEqual(out.strip(), "Scrapy %s" % ants.__version__)
