from sqlalchemy_utils import UUIDType
from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class TimeSpentStatus(db.Model, BaseMixin, SerializerMixin):
    """
    Describe the state of a given file.
    """

    name = db.Column(db.String(40), unique=False, nullable=False)
    short_name = db.Column(db.String(40), unique=True, nullable=False)


class TimeSpent(db.Model, BaseMixin, SerializerMixin):
    """
    Describes the time spent by someone on a task.
    """

    duration = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)

    task_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("task.id"), index=True
    )
    person_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("person.id"), index=True
    )
    description = db.Column(db.Text())
    validation_status_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("time_spent_status.id"),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "person_id", "task_id", "date", name="time_spent_uc"
        ),
    )
