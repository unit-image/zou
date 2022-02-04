from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class EntityStatus(db.Model, BaseMixin, SerializerMixin):
    """
    Describe the status of an entity.
    """

    name = db.Column(db.String(40), nullable=False)
    short_name = db.Column(
        db.String(10), unique=True, nullable=False, index=True
    )
    color = db.Column(db.String(7), nullable=False)
    shotgun_id = db.Column(db.Integer)
