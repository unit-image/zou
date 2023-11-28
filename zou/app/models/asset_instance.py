from sqlalchemy_utils import UUIDType
from sqlalchemy.dialects.postgresql import JSONB

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class AssetInstance(db.Model, BaseMixin, SerializerMixin):
    """
    An asset instance is the representation of an asset in a given asset or
    episode. It is useful for complex situations where an asset needs extra
    treatments only related to the given workspace.
    An asset can have multiple instances in an episode or asset (ex: a sword in
    a battle field).
    """

    asset_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("entity.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(80))
    number = db.Column(db.Integer())
    description = db.Column(db.String(200))
    active = db.Column(db.Boolean(), default=True)
    data = db.Column(JSONB)

    target_asset_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("entity.id"), index=True
    )
    episode_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("entity.id"), index=True
    )
    shotgun_id = db.Column(db.Integer)

    __table_args__ = (
        db.UniqueConstraint(
            "asset_id",
            "target_asset_id",
            "episode_id",
            "number",
            name="asset_instance_uc",
        ),
    )

    # Do not use these column. They are deprecated and will be dropped in
    # upcoming version
    entity_id = db.Column(UUIDType(binary=False), db.ForeignKey("entity.id"))
    entity_type_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("entity_type.id")
    )

    def __repr__(self):
        return "<AssetInstance %s>" % self.id
