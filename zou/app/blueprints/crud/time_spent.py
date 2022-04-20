from flask import request, abort
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

    def apply_filters(self, options):
        query = super(TimeSpentsResource, self).apply_filters(options)
        start_date = options.get("start_date", None)
        end_date = options.get("end_date", None)
        if not start_date and not end_date:
            return query

        if None in [start_date, end_date]:
            abort(
                400,
                "If querying for a range of dates, both a `start_date` and an "
                "`end_date` must be given.")

        return query.filter(self.model.date.between(start_date, end_date))


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
