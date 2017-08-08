from test.base import ApiTestCase

from zou import __version__
from zou.app.config import APP_NAME


class VersionTestCase(ApiTestCase):

    def test_version_route(self):
        data = self.get('/')
        self.assertEquals(data, {
            'api': APP_NAME,
            'version': __version__
        })
