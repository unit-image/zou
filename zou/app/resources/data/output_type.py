from zou.app.models.output_type import OutputType
from zou.app.resources.data.base import (
    BaseModelResource,
    BaseModelsResource
)


class OutputTypesResource(BaseModelsResource):

    def __init__(self):
        BaseModelsResource.__init__(self, OutputType)


class OutputTypeResource(BaseModelResource):

    def __init__(self):
        BaseModelResource.__init__(self, OutputType)
