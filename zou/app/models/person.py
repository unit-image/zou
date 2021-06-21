import sys

from sqlalchemy_utils import UUIDType, EmailType, LocaleType, TimezoneType
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.inspection import inspect

from pytz import timezone as pytz_timezone
from babel import Locale

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin
from zou.app.utils.fields import serialize_value


department_link = db.Table(
    "department_link",
    db.Column("person_id", UUIDType(binary=False), db.ForeignKey("person.id")),
    db.Column(
        "department_id", UUIDType(binary=False), db.ForeignKey("department.id")
    ),
)


class Person(db.Model, BaseMixin, SerializerMixin):
    """
    Describe a member of the studio (and an API user).
    """

    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(EmailType, unique=True)
    phone = db.Column(db.String(30))

    active = db.Column(db.Boolean(), default=True)
    last_presence = db.Column(db.Date())

    password = db.Column(db.LargeBinary(60))
    desktop_login = db.Column(db.String(80))
    shotgun_id = db.Column(db.Integer, unique=True)
    timezone = db.Column(
        TimezoneType(backend="pytz"), default=pytz_timezone("Europe/Paris")
    )
    locale = db.Column(LocaleType, default=Locale("en", "US"))
    data = db.Column(JSONB)
    role = db.Column(db.String(30), default="user")
    has_avatar = db.Column(db.Boolean(), default=False)

    notifications_enabled = db.Column(db.Boolean(), default=False)
    notifications_slack_enabled = db.Column(db.Boolean(), default=False)
    notifications_slack_userid = db.Column(db.String(60), default="")

    skills = db.relationship("Department", secondary=department_link)

    def __repr__(self):
        if sys.version_info[0] < 3:
            return "<Person %s>" % self.full_name().encode("utf-8")
        else:
            return "<Person %s>" % self.full_name()

    def full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def serialize(self, obj_type="Person", relations=False):
        """
        Overriding SerializeMixin's serialize method to filter out `created_by`
        and `updated_by` attributes, to avoid infinite recursion.
        """
        attrs = [
            attr for attr in inspect(self).attrs.keys()
            if attr not in ["created_by", "updated_by"]]

        if relations:
            data = {
                attr: serialize_value(getattr(self, attr)) for attr in attrs
            }
        else:
            data = {
                attr: serialize_value(getattr(self, attr))
                for attr in attrs
                if not self.is_join(attr)
            }
        data["type"] = obj_type or type(self).__name__
        data["full_name"] = self.full_name()
        return data

    def serialize_safe(self, relations=False):
        data = self.serialize("Person", relations=relations)
        del data["password"]
        return data

    def present_minimal(self, relations=False):
        data = self.serialize("Person", relations=relations)
        return {
            "id": data["id"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "full_name": data["full_name"],
            "has_avatar": data["has_avatar"],
            "active": data["active"]
        }

    @classmethod
    def create_from_import(cls, person):
        del person["type"]
        del person["full_name"]
        previous_person = cls.get(person["id"])
        if "password" in person:
            person["password"] = person["password"].encode()
        if previous_person is None:
            return (cls.create(**person), False)
        else:
            previous_person.update(person)
            return (previous_person, True)
