from flask import request, abort
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required

from zou.app.utils import query
from zou.app.project import asset_info, task_info, project_info

from zou.app.models.entity_type import EntityType
from zou.app.models.entity import Entity

from zou.app.project.exception import (
    ProjectNotFoundException,
    AssetTypeNotFoundException,
    AssetNotFoundException
)


class AssetResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve given asset.
        """
        try:
            asset = asset_info.get_asset(instance_id)
        except AssetNotFoundException:
            abort(404)
        return asset.serialize(obj_type="Asset")


class AssetsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self):
        """
        Retrieve all assets.
        """
        criterions = query.get_query_criterions_from_request(request)
        assets = asset_info.get_assets(criterions)
        return Entity.serialize_list(assets, obj_type="Asset")


class AllAssetsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self):
        """
        Retrieve all entities that are not shot or sequence.
        Adds project name and asset type name.
        """
        criterions = query.get_query_criterions_from_request(request)
        return asset_info.all_assets(criterions)


class AssetsAndTasksResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self):
        """
        Retrieve all entities that are not shot or sequence.
        Adds project name and asset type name and all related tasks.
        """
        criterions = query.get_query_criterions_from_request(request)
        return asset_info.all_assets_and_tasks(criterions)


class AssetTypeResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve given asset type.
        """
        try:
            asset_type = asset_info.get_asset_type(instance_id)
        except AssetTypeNotFoundException:
            abort(404)
        return asset_type.serialize(obj_type="AssetType")


class AssetTypesResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self):
        """
        Retrieve all asset types (entity types that are not shot, sequence or
        episode).
        """
        criterions = query.get_query_criterions_from_request(request)
        asset_types = asset_info.get_asset_types(criterions)
        return EntityType.serialize_list(asset_types, obj_type="AssetType")


class ProjectAssetTypesResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, project_id):
        """
        Retrieve all asset types for given project.
        """
        asset_types = asset_info.get_asset_types_for_project(project_id)
        return Entity.serialize_list(asset_types, obj_type="AssetType")


class ShotAssetTypesResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, shot_id):
        """
        Retrieve all asset shots for given soht.
        """
        asset_types = asset_info.get_asset_types_for_shot(shot_id)
        return Entity.serialize_list(asset_types, obj_type="AssetType")


class ProjectAssetsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, project_id):
        """
        Retrieve all assets for given project.
        """
        criterions = query.get_query_criterions_from_request(request)
        criterions["project_id"] = project_id
        assets = asset_info.get_assets(criterions)
        return Entity.serialize_list(assets, obj_type="Asset")


class ProjectAssetTypeAssetsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, project_id, asset_type_id):
        """
        Retrieve all assets for given project and entity type.
        """
        criterions = query.get_query_criterions_from_request(request)
        criterions["project_id"] = project_id
        criterions["entity_type_id"] = asset_type_id
        assets = asset_info.get_assets(criterions)
        return Entity.serialize_list(assets, obj_type="Asset")


class AssetTasksResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve all tasks related to a given shot.
        """
        try:
            return task_info.get_task_dicts_for_asset(instance_id)
        except AssetNotFoundException:
            abort(404)


class AssetTaskTypesResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve all task types related to a given asset.
        """
        try:
            asset = asset_info.get_asset(instance_id)
            return task_info.get_task_types_for_asset(asset)
        except AssetNotFoundException:
            abort(404)


class NewAssetResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def post(self, project_id, asset_type_id):
        (
            name,
            description
        ) = self.get_arguments()

        try:
            project = project_info.get_project(project_id)
            asset_type = asset_info.get_asset_type(asset_type_id)
            asset = asset_info.create_asset(
                project,
                asset_type,
                name,
                description
            )
        except ProjectNotFoundException:
            abort(404)
        except AssetTypeNotFoundException:
            abort(404)

        return asset.serialize(obj_type="Asset"), 201

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "name",
            help="The asset name is required.",
            required=True
        )
        parser.add_argument("description")
        args = parser.parse_args()

        return (
            args["name"],
            args.get("description", ""),
        )


class RemoveAssetResource(Resource):

    @jwt_required
    def delete(self, project_id, asset_type_id, asset_id):
        try:
            project = project_info.get_project(project_id)
            asset_type = asset_info.get_asset_type(asset_type_id)
            asset = asset_info.get_asset(asset_id)

            if asset.project_id != project.id:
                abort(404)

            if asset.entity_type_id != asset_type.id:
                abort(404)

            deleted_asset = asset_info.remove_asset(asset_id)
        except ProjectNotFoundException:
            abort(404)
        except AssetTypeNotFoundException:
            abort(404)
        except AssetNotFoundException:
            abort(404)

        return deleted_asset, 204
