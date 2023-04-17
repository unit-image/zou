from zou.app.models.event import ApiEvent

from .base import BaseModelResource, BaseModelsResource


class EventsResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, ApiEvent)


class EventResource(BaseModelResource):
    def __init__(self):
        BaseModelResource.__init__(self, ApiEvent)

    def serialize_instance(self, data):
        serialized_data = data.serialize()

        # Restore datetime microseconds for created_at field.
        # Otherwise event handlers might get stuck in a loop handling all events of
        # a second, not knowing which one is the last one.
        serialized_data['created_at'] = data['created_at']

        return serialized_data
