from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class FileStatus(db.Model, BaseMixin, SerializerMixin):
    """
    Describe the state of a given file.
    """

    name = db.Column(db.String(40), unique=True, nullable=False)
    short_name = db.Column(
        db.String(10), unique=True, nullable=False, index=True
    )
    color = db.Column(db.String(7), nullable=False)
    shotgun_id = db.Column(db.Integer)
