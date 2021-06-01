from zou.app.models.time_spent import TimeSpent, TimeSpentStatus

from .base import BaseModelsResource, BaseModelResource


class TimeSpentStatusesResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, TimeSpentStatus)

    def check_read_permissions(self):
        return True


class TimeSpentsResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, TimeSpent)


class TimeSpentResource(BaseModelResource):
    def __init__(self):
        BaseModelResource.__init__(self, TimeSpent)
