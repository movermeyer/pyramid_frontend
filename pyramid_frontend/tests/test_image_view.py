from unittest import TestCase

from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound

from ..images.view import ImageView


class TestImageView(TestCase):

    def test_view_notfound(self):
        with testing.testConfig():
            request = testing.DummyRequest()
            request.matchdict['prefix'] = 'aaaa'
            request.matchdict['name'] = 'nonexistent-image'
            request.matchdict['ext'] = 'jpg'
            with self.assertRaises(HTTPNotFound):
                ImageView(request)()