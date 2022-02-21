from flask import request
from flask_jwt_extended import jwt_required
from zou.app.models.time_spent import TimeSpent, TimeSpentStatus
from zou.app.utils import permissions
from zou.app.services import user_service

from .base import BaseModelsResource, BaseModelResource


class TimeSpentStatusesResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, TimeSpentStatus)

    def check_read_permissions(self):
        return True


class TimeSpentsResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, TimeSpent)

    def check_read_permissions(self):
        try:
            permissions.check_admin_permissions()
        except permissions.PermissionDenied as e:
            person_id = request.args.get("person_id", None)
            if not person_id:
                raise e

            user_service.check_person_access(person_id)

        return True


class TimeSpentResource(BaseModelResource):
    def __init__(self):
        BaseModelResource.__init__(self, TimeSpent)

    def check_read_permissions(self, instance):
        try:
            permissions.check_admin_permissions()
        except permissions.PermissionDenied as e:
            person_id = request.args.get("person_id", None)
            if not person_id:
                raise e

            user_service.check_person_access(person_id)

        return True
