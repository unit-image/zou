from zou.app.models.entity_status import EntityStatus
from .base import BaseModelResource, BaseModelsResource


class EntityStatusesResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, EntityStatus)

    def check_read_permissions(self):
        return True


class EntityStatusResource(BaseModelResource):
    def __init__(self):
        BaseModelResource.__init__(self, EntityStatus)

    def check_read_permissions(self, instance):
        return True
