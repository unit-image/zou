from sqlalchemy_utils import UUIDType
from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class DayWorked(db.Model, BaseMixin, SerializerMixin):
    """
    Describes the day worked by a person.
    """
    date = db.Column(db.Date, nullable=False)

    person_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("person.id"), index=True
    )

    work_duration = db.Column(db.Float, default=1)

    variable_time = db.Column(db.Integer, default=0)

    justification = db.Column(db.Text())

    __table_args__ = (
        db.UniqueConstraint(
            "person_id", "date", name="day_worked_uc"
        ),
    )


class WorkLocation(db.Model, BaseMixin, SerializerMixin):
    """
    Describes the location where a person can work.
    """
    name = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
        index=True,
        default="undefined")
