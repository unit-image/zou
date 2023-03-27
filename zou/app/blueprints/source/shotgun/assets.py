from flask_restful import current_app

from sqlalchemy.exc import IntegrityError

from zou.app.models.project import Project
from zou.app.models.entity import Entity
from zou.app.models.entity_type import EntityType
from zou.app.models.entity_status import EntityStatus

from zou.app.blueprints.source.shotgun.base import (
    BaseImportShotgunResource,
    ImportRemoveShotgunBaseResource,
)

from zou.app.services import (
    assets_service,
    deletion_service,
    tasks_service,
    files_service,
)

from zou.app.services.exception import AssetNotFoundException


class ImportShotgunAssetsResource(BaseImportShotgunResource):
    def __init__(self):
        BaseImportShotgunResource.__init__(self)

    def prepare_import(self):
        entity_type_names = self.extract_entity_type_names(self.sg_entries)
        assets_service.create_asset_types(entity_type_names)
        self.project_ids = Project.get_id_map()
        self.entity_type_ids = EntityType.get_id_map(field="name")
        self.entity_status_ids = EntityStatus.get_id_map(field="short_name")
        self.parent_map = {}

    def extract_entity_type_names(self, sg_assets):
        return {
            x["sg_asset_type"]
            for x in sg_assets
            if x["sg_asset_type"] is not None
        }

    def extract_data(self, sg_asset):
        entity_type_id = self.entity_type_ids.get(
            sg_asset["sg_asset_type"], None
        )
        project_id = self.project_ids.get(sg_asset["project"]["id"], None)
        parent_shotgun_ids = [
            asset["id"] for asset in sg_asset.get("parents", [])
        ]
        entity_status_id = self.entity_status_ids.get(
            sg_asset["sg_status_list"], None
        )

        return {
            "name": sg_asset["code"],
            "shotgun_id": sg_asset["id"],
            "description": sg_asset["description"],
            "entity_type_id": entity_type_id,
            "project_id": project_id,
            "parent_shotgun_ids": parent_shotgun_ids,
            "entity_status_id": entity_status_id,
        }

    def import_entry(self, data):
        entity = None
        parent_shotgun_ids = data["parent_shotgun_ids"]
        del data["parent_shotgun_ids"]

        try:
            entity = self.save_entity(data)
        except IntegrityError:
            current_app.logger.error(
                "Similar asset already exists "
                "or project is missing: %s" % data
            )

        if entity is not None:
            # Setting all parents every time, to ensure that parent removal works properly.
            parents = [
                Entity.get_by(shotgun_id=parent_shotgun_id)
                for parent_shotgun_id in parent_shotgun_ids
            ]
            # Preserve entities_in that are not assets, since entities_in does not
            # contain only parent assets.
            parents.extend([
                parent_entity
                for parent_entity in entity.entities_in
                if not assets_service.is_asset(parent_entity)
            ])

            assets_service.update_asset(entity.id, {"entities_in": parents})

        return entity

    def save_entity(self, data):
        entity = None
        try:
            entity = assets_service.get_raw_asset_by_shotgun_id(
                data["shotgun_id"]
            )
            entity.update(data)
            assets_service.clear_asset_cache(str(entity.id))
            current_app.logger.info("Entity updated: %s" % entity)
        except AssetNotFoundException:
            if data.get("entity_type_id", None) is not None:
                entity = Entity(**data)
                entity.save()
                current_app.logger.info("Entity created: %s" % entity)
            else:
                current_app.logger.info("Entity ignored: %s" % data["name"])
        return entity


class ImportRemoveShotgunAssetResource(ImportRemoveShotgunBaseResource):
    def __init__(self):
        ImportRemoveShotgunBaseResource.__init__(self, Entity, self.delete_func)

    def delete_func(self, asset):
        try:
            asset = assets_service.get_asset_by_shotgun_id(asset.shotgun_id)
            tasks = tasks_service.get_tasks_for_asset(asset["id"])
            if self.is_working_files_linked(tasks):
                assets_service.cancel_asset(asset["id"])
            else:
                for task in tasks:
                    deletion_service.remove_task(task["id"])
                assets_service.remove_asset(asset["id"])
            return asset
        except AssetNotFoundException:
            return None

    def is_working_files_linked(self, tasks):
        is_working_files = False
        for task in tasks:
            working_files = files_service.get_working_files_for_task(task["id"])
            if len(working_files) > 0:
                is_working_files = True
                break
        return is_working_files
