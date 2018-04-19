from zou.app.utils import events
from zou.app.services import base_service

from zou.app.models.entity import Entity
from zou.app.models.entity_type import EntityType
from zou.app.models.preview_file import PreviewFile

from zou.app.services.exception import (
    PreviewFileNotFoundException,
    EntityNotFoundException,
    EntityTypeNotFoundException
)


def get_entity_type(entity_type_id):
    """
    Return an entity type matching given id, as a dict. Raises an exception
    if nothing is found.
    """
    return base_service.get_instance(
        EntityType,
        entity_type_id,
        EntityTypeNotFoundException
    ).serialize()


def get_entity_type_by_name(name):
    """
    Return entity type maching *name*. If it doesn't exist, it creates it.
    """
    entity_type = EntityType.get_by(name=name)
    if entity_type is None:
        entity_type = EntityType.create(name=name)
    return entity_type.serialize()


def get_entity_raw(entity_id):
    """
    Return an entity type matching given id, as an active record. Raises an
    exception if nothing is found.
    """
    return base_service.get_instance(
        Entity,
        entity_id,
        EntityNotFoundException
    )


def get_entity(entity_id):
    """
    Return an entity type matching given id, as a dict. Raises an exception if
    nothing is found.
    """
    return base_service.get_instance(
        Entity,
        entity_id,
        EntityNotFoundException
    ).serialize()


def update_entity_preview(entity_id, preview_file_id):
    """
    Update given entity main preview. If entity or preview is not found, it
    raises an exception.
    """
    entity = Entity.get(entity_id)
    if entity is None:
        raise EntityNotFoundException

    preview_file = PreviewFile.get(preview_file_id)
    if preview_file is None:
        raise PreviewFileNotFoundException

    entity.update({"preview_file_id": preview_file.id})
    events.emit("preview-file:set-main", {
        "entity_id": entity_id,
        "preview_file_id": preview_file_id
    })
    return entity.serialize()
