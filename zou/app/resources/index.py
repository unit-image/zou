from flask_restful import Resource
from zou import __version__

from zou.app.config import APP_NAME


class IndexResource(Resource):
    def get(self):
        return {
            'api': APP_NAME,
            'version': __version__
        }
