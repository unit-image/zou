import copy

from zou.app.models.output_file import OutputFile
from zou.app.models.entity import Entity
from zou.app.models.project import Project
from zou.app.services import (
    user_service,
    entities_service,
    persons_service,
)
from zou.app.utils import permissions, events
from zou.app.services.exception import ArgumentsException

from .base import BaseModelsResource, BaseModelResource


class OutputFilesResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, OutputFile)

    def check_read_permissions(self):
        user_service.block_access_to_vendor()
        return True

    def add_project_permission_filter(self, query):
        if permissions.has_admin_permissions():
            return query
        else:
            query = (
                query.join(Entity, OutputFile.entity_id == Entity.id)
                .join(Project)
                .filter(user_service.build_related_projects_filter())
            )
            return query


class OutputFileResource(BaseModelResource):
    def __init__(self):
        BaseModelResource.__init__(self, OutputFile)

    def check_read_permissions(self, instance):
        entity = entities_service.get_entity(instance["entity_id"])
        user_service.check_project_access(entity["project_id"])
        user_service.check_entity_access(entity["id"])

        return True

    def check_update_permissions(self, output_file, data):
        if permissions.has_manager_permissions():
            return True

        current_user = persons_service.get_current_user()
        if output_file["person_id"] == current_user["id"]:
            return True

        return user_service.check_working_on_entity(
            output_file["temporal_entity_id"] or output_file["entity_id"]
        )

    def pre_update(self, instance_dict: dict, data: dict):
        """
        Validates the update data and prepares the event update data.

        :param instance_dict: The serialized object.
        :param data: The update data.
        :raises ArgumentsException: When the given update parameters are unsupported.
        """
        if "downstreams" in data:
            raise ArgumentsException(
                "Cannot update downstreams directly. Please update the upstreams instead."
            )

        if "upstreams" in data:
            updated_upstreams = set(data["upstreams"])
            instance = self.model.get(instance_dict["id"])
            current_upstreams = set(instance.serialize_relations().get("upstreams", []))
            if current_upstreams == updated_upstreams:
                data.pop("upstreams")

        self.event_update_data = copy.deepcopy(data)

    def update_data(self, data: dict, instance_id: str) -> dict:
        """
        Converts the data into database-compatible data.

        :param data: The data.
        :param instance_id: The object's id.
        :returns: The converted data.
        """
        if "upstreams" in data:
            updated_upstreams_ids = list(set(data["upstreams"]))
            data["upstreams"] = [
                OutputFile.get_by(id=upstream_id)
                for upstream_id in updated_upstreams_ids
            ]

        return data

    def emit_update_event(self, instance_dict: dict):
        """
        Emits the update event with the update information.

        :param instance_dict: The serialized object.
        """
        self.event_update_data["output_file_id"] = instance_dict["id"]
        events.emit(
            "output-file:update",
            self.event_update_data,
            project_id=instance_dict.get("project_id", None),
        )
