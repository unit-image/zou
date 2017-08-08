import os

from flask import abort
from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required

from zou.app.models.working_file import WorkingFile

from zou.app.resources.data.base import BaseModelResource

from zou.app.project import file_info, task_info, person_info, file_tree

from zou.app.project.exception import (
    TaskNotFoundException,
    OutputFileNotFoundException,
    OutputTypeNotFoundException,
    WorkingFileNotFoundException,
    PersonNotFoundException,
    MalformedFileTreeException
)


class CommentWorkingFileResource(BaseModelResource):

    def __init__(self):
        BaseModelResource.__init__(self, WorkingFile)

    @jwt_required
    def put(self, working_file_id):
        comment = self.get_comment_from_args()
        working_file = self.update_comment(working_file_id, comment)
        return working_file.serialize(), 200

    def get_comment_from_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "comment",
            required=True,
            help="Comment field expected."
        )
        args = parser.parse_args()
        comment = args["comment"]
        return comment

    def update_comment(self, working_file_id, comment):
        working_file = self.get_model_or_404(working_file_id)
        working_file.update({
            "comment": comment
        })
        return working_file


class PublishFileResource(Resource):

    @jwt_required
    def post(self, task_id, working_file_id):
        (
            comment,
            person_id,
            software,
            output_type_id,
            scene,
            separator
        ) = self.get_arguments()
        separator = "/"

        try:
            task = task_info.get_task(task_id)
            output_type = file_info.get_output_type(output_type_id)
            working_file = file_info.get_working_file(working_file_id)
            person = person_info.get_person(person_id)

            output_file_dict = file_info.create_new_output_revision(
                task.entity_id,
                task.id,
                working_file.id,
                output_type.id,
                person.id,
                comment,
                name=working_file.name
            )
            output_file = file_info.get_output_file(output_file_dict["id"])

            output_file_dict = self.add_path_info(
                output_file,
                output_file_dict,
                "output",
                task,
                software,
                output_type,
                scene,
                separator
            )
            output_file_dict["preview_path"] = self.get_preview_path(
                task,
                output_file_dict["revision"],
                separator
            )

            task_info.to_review_task(task, output_file_dict)

        except TaskNotFoundException:
            abort(404)

        except WorkingFileNotFoundException:
            abort(404)

        except OutputTypeNotFoundException:
            return {"error": "Cannot find given output type."}, 400

        except PersonNotFoundException:
            return {"error": "Cannot find given person."}, 400

        return output_file_dict, 201

    def get_arguments(self):
        parser = reqparse.RequestParser()
        output_type = file_info.get_or_create_output_type("Geometry")
        parser.add_argument("output_type_id", default=output_type.id)
        parser.add_argument("person_id", default="")
        parser.add_argument("software", default="3dsmax")
        parser.add_argument("comment", default="")
        parser.add_argument("scene", default=1)
        parser.add_argument("separator", default="/")
        args = parser.parse_args()

        return (
            args["comment"],
            args["person_id"],
            args["software"],
            args["output_type_id"],
            args["scene"],
            args["separator"]
        )

    def add_path_info(
        self,
        file_model,
        file_dict,
        mode,
        task,
        software,
        output_type,
        scene,
        name,
        separator=os.sep
    ):
        folder_path = file_tree.get_folder_path(
            task,
            mode=mode,
            software=software,
            output_type=output_type,
            scene=scene,
            name=name,
            sep=separator
        )
        file_name = file_tree.get_file_name(
            task,
            mode=mode,
            version=file_dict["revision"],
            software=software,
            output_type=output_type,
            name=name,
            scene=scene
        )

        file_dict.update({
            "folder_path": folder_path,
            "file_name": file_name
        })

        file_model.update({
            "path": "%s%s%s" % (folder_path, separator, file_name)
        })

        return file_dict

    def get_preview_path(self, task, revision, separator=os.sep):
        try:
            folder_path = file_tree.get_folder_path(
                task,
                mode="preview",
                sep=separator
            )
            file_name = file_tree.get_file_name(
                task,
                mode="preview",
                version=revision
            )

            return {
                "folder_path": folder_path,
                "file_name": file_name
            }
        except MalformedFileTreeException:  # No template for preview files.
            return {
                "folder_path": "",
                "file_name": ""
            }


class GetNextOutputFileResource(Resource):

    @jwt_required
    def get(self, task_id, output_type_id):
        try:
            task = task_info.get_task(task_id)
            output_type = file_info.get_output_type(output_type_id)
        except TaskNotFoundException:
            abort(404)
        except OutputFileNotFoundException:
            abort(404)

        next_revision_number = \
            file_info.get_next_output_file_revision(task.id, output_type.id)

        return {
            "next_revision": next_revision_number
        }, 200


class LastWorkingFilesResource(Resource):

    @jwt_required
    def get(self, task_id):

        result = {}
        try:
            task = task_info.get_task(task_id)
            result = file_info.get_last_working_files_for_task(task.id)
        except TaskNotFoundException:
            abort(404)

        return result


class NewWorkingFileResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def post(self, task_id):
        (
            name,
            description,
            comment,
            person_id,
            sep
        ) = self.get_arguments()

        try:
            task = task_info.get_task(task_id)
            revision = file_info.get_next_working_revision(task_id, name)
            path = self.build_path(task, name, revision, sep)
            if person_id is None:
                person = person_info.get_current_user()
                person_id = person.id

            working_file = file_info.create_new_working_revision(
                task_id,
                person_id,
                name=name,
                path=path,
                comment=comment,
                revision=revision
            )
        except TaskNotFoundException:
            abort(404)

        return working_file, 201

    def build_path(self, task, name, revision, sep):
        folder_path = file_tree.get_folder_path(
            task,
            name=name
        )
        file_name = file_tree.get_file_name(
            task,
            name=name,
            version=revision
        )
        return "%s%s%s" % (folder_path, sep, file_name)

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "name",
            help="The asset name is required.",
            required=True
        )
        parser.add_argument("description")
        parser.add_argument("comment")
        parser.add_argument("person_id")
        parser.add_argument("sep", default="/")
        args = parser.parse_args()

        return (
            args["name"],
            args.get("description", ""),
            args.get("comment", ""),
            args.get("person_id", ""),
            args.get("sep", "")
        )
