from zou.app.models.day_worked import DayWorked
from .base import BaseModelsResource, BaseModelResource


class DaysWorkedResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, DayWorked)


class DayWorkedResource(BaseModelResource):
    def __init__(self):
        BaseModelResource.__init__(self, DayWorked)
