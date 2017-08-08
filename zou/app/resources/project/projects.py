from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.project import project_info
from zou.app.utils import fields


class OpenProjectsResource(Resource):

    @jwt_required
    def get(self):
        return fields.serialize_models(project_info.open_projects())


class AllProjectsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self):
        return project_info.all_projects(), 200
