from flask import request, abort
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required

from zou.app.project import (
    file_tree,
    project_info,
    task_info,
    file_info
)
from zou.app.project.exception import (
    OutputFileNotFoundException,
    ProjectNotFoundException,
    SequenceNotFoundException,
    TaskNotFoundException,
    WrongFileTreeFileException,
    WrongPathFormatException,
    MalformedFileTreeException
)


class FolderPathResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def post(self):
        (
            mode,
            task_id,
            software,
            output_type_id,
            scene,
            name,
            separator
        ) = self.get_arguments()

        try:
            task = task_info.get_task(task_id)
            output_type = file_info.get_output_type(output_type_id)
            path = file_tree.get_folder_path(
                task,
                mode=mode,
                software=software,
                output_type=output_type,
                scene=scene,
                name=name,
                sep=separator
            )

        except TaskNotFoundException:
            return {
                "error": "Given task does not exist.",
                "received_data": request.json,
            }, 400

        except SequenceNotFoundException:
            return {
                "error": "Sequence for shot linked to task not found.",
                "received_data": request.json,
                "path": None
            }, 400

        except OutputFileNotFoundException:
            return {
                "error": "Given output type does not exist.",
                "received_data": request.json,
            }, 400

        except MalformedFileTreeException:
            return {
                "error":
                    "Tree is not properly written, check modes and variables",
                "received_data": request.json,
            }, 400

        return {"path": path}, 200

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "mode",
            help="The file mode is required (working, output,...).",
            required=True
        )
        parser.add_argument(
            "task_id",
            help="The task file id is required.",
            required=True
        )
        geometry_type = file_info.get_or_create_output_type("geometry")
        parser.add_argument("sep", default="/")
        parser.add_argument("software", default="3dsmax")
        parser.add_argument("output_type_id", default=geometry_type.id)
        parser.add_argument("scene", default=1)
        parser.add_argument("name", default="name")
        args = parser.parse_args()

        return (
            args["mode"],
            args["task_id"],
            args["software"],
            args["output_type_id"],
            args["scene"],
            args["name"],
            args["sep"],
        )


class FilePathResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def post(self):
        (
            mode,
            task_id,
            version,
            comment,
            software,
            output_type_id,
            scene,
            name,
            separator
        ) = self.get_arguments()

        try:
            task = task_info.get_task(task_id)
            output_type = file_info.get_output_type(output_type_id)
            is_version_set_by_user = version == 0
            if is_version_set_by_user and mode == "working":
                version = self.get_next_version(task_id, name)

            file_path = file_tree.get_folder_path(
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
                version=version,
                software=software,
                output_type=output_type,
                scene=scene,
                name=name
            )
        except TaskNotFoundException:
            return {
                "error": "Given task does not exist.",
                "received_data": request.json,
            }, 400

        except SequenceNotFoundException:
            return {
                "error": "Sequence for shot linked to task not found.",
                "received_data": request.json,
            }, 400

        except MalformedFileTreeException:
            return {
                "error":
                    "Tree is not properly written, check modes and variables",
                "received_data": request.json,
            }, 400

        except OutputFileNotFoundException:
            return {
                "error": "Given output type does not exist.",
                "received_data": request.json,
            }, 400

        return {"path": file_path, "name": file_name}, 200

    def get_next_version(self, task_id, name):
        last_working_files = \
            file_info.get_last_working_files_for_task(task_id)
        working_file = last_working_files.get(name, None)
        if working_file is not None:
            version = working_file["revision"] + 1
        else:
            version = 1
        return version

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "mode",
            help="The file mode is required (working, output,...).",
            required=True
        )
        parser.add_argument(
            "task_id",
            help="The task file id is required (working, output,...).",
            required=True
        )
        geometry_type = file_info.get_or_create_output_type("geometry")
        parser.add_argument("comment", default="")
        parser.add_argument("version", default=0)
        parser.add_argument("software", default="3dsmax")
        parser.add_argument("output_type_id", default=geometry_type.id)
        parser.add_argument("scene", default=1)
        parser.add_argument("name", default="")
        parser.add_argument("sep", default="/")
        args = parser.parse_args()

        return (
            args["mode"],
            args["task_id"],
            args["version"],
            args["comment"],
            args["software"],
            args["output_type_id"],
            args["scene"],
            args["name"],
            args["sep"]
        )


class SetTreeResource(Resource):

    @jwt_required
    def post(self, project_id):
        (tree_name) = self.get_arguments()

        try:
            project = project_info.get_project(project_id)
            tree = file_tree.get_tree_from_file(tree_name)
        except ProjectNotFoundException:
            abort(404)
        except WrongFileTreeFileException:
            abort(400, "Selected tree is not available")

        project.update({"file_tree": tree})
        return project.serialize()

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "tree_name",
            help="The name of the tree to set is required.",
            required=True
        )
        args = parser.parse_args()

        return (
            args.get("tree_name", ""),
        )


class GetTaskFromPathResource(Resource):

    @jwt_required
    def post(self):
        (
            file_path,
            project_id,
            path_type,
            mode,
            sep
        ) = self.get_arguments()
        try:
            project = project_info.get_project(project_id)
        except ProjectNotFoundException:
            return {
                "error": "Given project does not exist.",
                "received_data": request.json,
            }, 400

        try:
            if path_type == "shot":
                task = file_tree.get_shot_task_from_path(
                    file_path,
                    project,
                    mode,
                    sep
                )
            else:
                task = file_tree.get_asset_task_from_path(
                    file_path,
                    project,
                    mode,
                    sep
                )

        except WrongPathFormatException:
            return {
                "error": "The given path lacks of information..",
                "received_data": request.json
            }, 400
        except TaskNotFoundException:
            return {
                "error": "No task exist for this path.",
                "received_data": request.json
            }, 400

        return task.serialize()

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "file_path",
            help="The file path is required.",
            required=True
        )
        parser.add_argument(
            "project_id",
            help="The project ID is required.",
            required=True
        )
        parser.add_argument(
            "type",
            help="The type (asset or shot) is required.",
            required=True
        )
        parser.add_argument("mode", "working")
        parser.add_argument("sep", "/")
        args = parser.parse_args()

        return (
            args["file_path"],
            args["project_id"],
            args["type"],
            args["mode"],
            args["sep"]
        )
