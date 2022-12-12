from zou.app.models.output_file import OutputFileStream
from zou.app.utils import fields

from .base import BaseModelResource, BaseModelsResource
from zou.app.services.exception import (
    OutputFileStreamNotFoundException,
    WrongParameterException
)


class OutputFileStreamsResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, OutputFileStream)


class OutputFileStreamResource(BaseModelResource):
    def __init__(self):
        BaseModelResource.__init__(self, OutputFileStream)

    def get_model_or_404(self, instance_id):
        if not fields.is_valid_id(instance_id):
            raise WrongParameterException("Malformed ID.")
        instance = self.model.get_by(id=instance_id)
        if instance is None:
            raise OutputFileStreamNotFoundException
        return instance
