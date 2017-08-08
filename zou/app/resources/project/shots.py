from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.models.entity import Entity
from zou.app.models.task import Task
from zou.app.models.task_type import TaskType

from zou.app.project import shot_info, task_info, project_info
from zou.app.utils import query

from zou.app.project.exception import (
    ShotNotFoundException,
    ProjectNotFoundException
)


class ShotResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve given shot.
        """
        try:
            shot = shot_info.get_shot(instance_id)
        except ShotNotFoundException:
            abort(404)
        return shot.serialize(obj_type="Shot")


class ShotsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self):
        """
        Retrieve all shot entries. Filters can be specified in the query string.
        """
        criterions = query.get_query_criterions_from_request(request)
        return shot_info.get_shots(criterions)


class ShotAssetsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve all assets for a given shot.
        """
        try:
            shot = shot_info.get_shot(instance_id)
        except ShotNotFoundException:
            abort(404)

        return Entity.serialize_list(shot.entities_out, obj_type="Asset")


class ShotTaskTypesResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve all task types related to a given shot.
        """
        tasks = Task.query.filter_by(entity_id=instance_id).all()

        task_types = []
        if len(tasks) > 0:
            task_type_ids = map(lambda x: x.task_type_id, tasks)
            task_types = TaskType.query.filter(TaskType.id.in_(task_type_ids))

        return TaskType.serialize_list(task_types)


class ShotTasksResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve all tasks related to a given shot.
        """
        try:
            return task_info.get_task_dicts_for_shot(instance_id)
        except ShotNotFoundException:
            abort(404)


class ShotsAndTasksResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self):
        """
        Retrieve all shots, adds project name and asset type name and all
        related tasks.
        """
        criterions = query.get_query_criterions_from_request(request)
        return shot_info.get_shots_and_tasks(criterions)


class ProjectShotsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, project_id):
        """
        Retrieve all shots related to a given project.
        """
        try:
            project = project_info.get_project(project_id)
            return Entity.serialize_list(
                shot_info.get_shots_for_project(project),
                obj_type="Shot"
            )
        except ProjectNotFoundException:
            abort(404)


class ProjectSequencesResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, project_id):
        """
        Retrieve all sequences related to a given project.
        """
        try:
            project = project_info.get_project(project_id)
            return Entity.serialize_list(
                shot_info.get_sequences_for_project(project),
                obj_type="Sequence"
            )
        except ProjectNotFoundException:
            abort(404)


class ProjectEpisodesResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, project_id):
        """
        Retrieve all episodes related to a given project.
        """
        try:
            project = project_info.get_project(project_id)
            return Entity.serialize_list(
                shot_info.get_episodes_for_project(project),
                obj_type="Episode"
            )
        except ProjectNotFoundException:
            abort(404)
