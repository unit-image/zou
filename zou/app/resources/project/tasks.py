from flask import abort, request
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required

from zou.app.models.task import Task
from zou.app.models.task_status import TaskStatus
from zou.app.models.comment import Comment
from zou.app.models.person import Person
from zou.app.models.preview_file import PreviewFile

from zou.app.project.exception import (
    TaskNotFoundException,
    TaskTypeNotFoundException
)
from zou.app.project import task_info, shot_info, asset_info
from zou.app.utils import query


class CommentTaskResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def post(self, task_id):
        (
            task_status_id,
            comment
        ) = self.get_arguments()

        task = Task.get(task_id)
        task_status = TaskStatus.get(task_status_id)
        person = Person.get(person_info.get_current_user().id)
        comment = Comment.create(
            object_id=task_id,
            object_type="Task",
            task_status_id=task_status_id,
            person_id=person_info.get_current_user().id,
            text=comment
        )
        task.update({"task_status_id": task_status_id})
        comment_dict = comment.serialize()
        comment_dict["task_status"] = task_status.serialize()
        comment_dict["person"] = person.serialize()

        return comment_dict, 201

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "task_status_id",
            required=True,
            help="Task Status ID is missing"
        )
        parser.add_argument("comment", default="")
        args = parser.parse_args()

        return (
            args["task_status_id"],
            args["comment"]
        )


class AddPreviewResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def post(self, task_id, comment_id):
        task = Task.get(task_id)
        comment = Comment.get(comment_id)
        task_status = TaskStatus.get(comment.task_status_id)
        person = Person.get(person_info.get_current_user().id)

        if task_status.short_name != "wfa":
            return {"error": "Comment status is not waiting for approval."}, 400

        revision = task_info.get_next_preview_revision(task_id)
        preview = PreviewFile.create(
            name=task.name,
            revision=revision,
            source="webgui",
            task_id=task.id,
            person_id=person.id
        )
        comment.update({"preview_file_id": preview.id})

        return preview.serialize(), 201


class TaskPreviewsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, task_id):
        try:
            task = task_info.get_task(task_id)
            previews = PreviewFile.filter_by(
                task_id=task.id
            ).order_by(
                PreviewFile.revision.desc()
            )
        except TaskNotFoundException:
            abort(404)

        return PreviewFile.serialize_list(previews)


class TaskCommentsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, task_id):
        try:
            comments = []
            task = task_info.get_task(task_id)
            query = Comment.query.order_by(Comment.created_at.desc())
            query = query.filter_by(
                object_id=task.id
            )
            query = query.join(Person)
            query = query.join(TaskStatus)
            query = query.add_columns(TaskStatus.name)
            query = query.add_columns(TaskStatus.short_name)
            query = query.add_columns(TaskStatus.color)
            query = query.add_columns(Person.first_name)
            query = query.add_columns(Person.last_name)
            results = query.all()

            for result in results:
                (
                    comment,
                    task_status_name,
                    task_status_short_name,
                    task_status_color,
                    person_first_name,
                    person_last_name
                ) = result

                comment_dict = comment.serialize()
                comment_dict["person"] = {
                    "first_name": person_first_name,
                    "last_name": person_last_name,
                    "id": str(comment.person_id)
                }
                comment_dict["task_status"] = {
                    "name": task_status_name,
                    "short_name": task_status_short_name,
                    "color": task_status_color,
                    "id": str(comment.task_status_id)
                }

                if comment.preview_file_id is not None:
                    preview = PreviewFile.get(comment.preview_file_id)
                    comment_dict["preview"] = {
                        "id": str(preview.id),
                        "revision": preview.revision
                    }

                comments.append(comment_dict)

        except TaskNotFoundException:
            abort(404)

        return comments


class CreateShotTasksResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def post(self, task_type_id):
        try:
            criterions = query.get_query_criterions_from_request(request)
            shots = shot_info.get_shots(criterions)
            task_type = task_info.get_task_type(task_type_id)
            tasks = [task_info.create_task(task_type, shot) for shot in shots]

        except TaskTypeNotFoundException:
            abort(404)

        return tasks, 201


class CreateAssetTasksResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def post(self, task_type_id):
        try:
            criterions = query.get_query_criterions_from_request(request)
            assets = asset_info.get_assets(criterions)
            task_type = task_info.get_task_type(task_type_id)
            tasks = [
                task_info.create_task(task_type, asset.serialize())
                for asset in assets
            ]

        except TaskTypeNotFoundException:
            abort(404)

        return tasks, 201
