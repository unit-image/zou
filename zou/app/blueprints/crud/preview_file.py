from zou.app.models.entity import Entity
from zou.app.models.preview_file import PreviewFile
from zou.app.models.project import Project
from zou.app.models.task import Task
from zou.app.services import tasks_service, user_service
from zou.app.utils import permissions

from .base import BaseModelsResource, BaseModelResource


class PreviewFilesResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, PreviewFile)

    def add_project_permission_filter(self, query):
        """
        Filtering to keep only the files from projects available to the user's
        team. Allows projects that are no longer open.
        """
        if permissions.has_admin_permissions():
            return query
        else:
            query = (
                query.join(Task, PreviewFile.task_id == Task.id)
                .join(Entity, Task.entity_id == Entity.id)
                .join(Project)
                .filter(user_service.build_team_filter())
            )
            return query

    def check_read_permissions(self):
        """
        Overriding so that people without admin credentials can still access
        this resource.
        """
        user_service.block_access_to_vendor()
        return True


class PreviewFileResource(BaseModelResource):
    def __init__(self):
        BaseModelResource.__init__(self, PreviewFile)

    def check_read_permissions(self, preview_file):
        task = tasks_service.get_task(preview_file["task_id"])
        user_service.check_project_access(task["project_id"])
        user_service.check_entity_access(task["entity_id"])
        return True

    def check_update_permissions(self, preview_file, data):
        task = tasks_service.get_task(preview_file["task_id"])
        user_service.check_project_access(task["project_id"])
        user_service.check_entity_access(task["entity_id"])
        return True
