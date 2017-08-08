from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class Software(db.Model, BaseMixin, SerializerMixin):
    name = db.Column(db.String(40), unique=True, nullable=False)
    short_name = db.Column(db.String(20), nullable=False)
    file_extension = db.Column(db.String(20), nullable=False)
