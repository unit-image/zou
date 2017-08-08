import datetime
import uuid
import sqlalchemy.orm as orm

from pytz import timezone
from babel import Locale


def serialize_value(value):
    """
    Utility function to handle the parsing of specific fields.
    """
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    elif isinstance(value, uuid.UUID):
        return str(value)
    elif isinstance(value, dict):
        return serialize_dict(value)
    elif isinstance(value, orm.collections.InstrumentedList):
        return serialize_orm_arrays(value)
    elif isinstance(value, bytes):
        return value.decode("utf-8")
    elif isinstance(value, str):
        return value
    elif isinstance(value, int):
        return value
    elif isinstance(value, Locale):
        return str(value)
    elif isinstance(value, type(timezone("Europe/Paris"))):
        return str(value)
    elif isinstance(value, list):
        return serialize_list(value)
    elif value is None:
        return None
    elif isinstance(value, object):
        return value.serialize()
    else:
        return value


def serialize_list(list_value):
    return [serialize_value(value) for value in list_value]


def serialize_dict(dict_value):
    """
    Serialize a dict into simple data structures (useful for json dumping).
    """
    result = {}
    for key in dict_value.keys():
        result[key] = serialize_value(dict_value[key])

    return result


def serialize_orm_arrays(array_value):
    """
    Serialize a orm array into simple data structures (useful for json dumping).
    """
    result = []
    for val in array_value:
        result.append(serialize_value(val.id))
    return result


def serialize_models(models):
    """
    Serialize a list of models
    """
    return [model.serialize() for model in models if model is not None]


def gen_uuid():
    """
    Generate a unique identifier.
    """
    return uuid.uuid4()


def get_date_object(date_string, date_format="%Y-%m-%d"):
    """
    Shortcut for date parsing.
    """
    return datetime.datetime.strptime(date_string, date_format)
