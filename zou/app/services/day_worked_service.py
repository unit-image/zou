import datetime
from dateutil import relativedelta

from sqlalchemy.exc import DataError
from zou.app.models.day_worked import DayWorked, WorkLocation
from zou.app.utils import events
from zou.app.services.exception import WrongDateFormatException

from zou.app.services.base_service import (
    get_or_create_instance_by_name,
)


def create_or_update_day_worked(
        person_id,
        date,
        work_duration=100,
        variable_time=0,
        justification=None,
        work_location_id=None):
    """
    Create a new time spent if it doesn't exist. If it exists, it updates it
    with the new duration and returns it from the database.
    """
    try:
        day_worked = DayWorked.get_by(
            person_id=person_id,
            date=date
        )
    except DataError:
        raise WrongDateFormatException

    if day_worked is not None:
        if work_duration is not None:
            day_worked.update({"work_duration": work_duration})

        if variable_time is not None:
            day_worked.update({"variable_time": variable_time})

        if justification:
            day_worked.update({"justification": justification})

        if work_location_id:
            day_worked.update({"work_location_id": work_location_id})

        events.emit(
            "day_worked:update",
            {"day_worked_id": str(day_worked.id)}
        )
    else:
        if work_location_id is None:
            undefined_work_location = get_or_create_work_location("undefined")
            work_location_id = undefined_work_location["id"]

        day_worked = DayWorked.create(
            person_id=person_id,
            date=date,
            work_duration=work_duration,
            variable_time=variable_time,
            justification=justification,
            work_location_id=work_location_id,
        )
        events.emit(
            "day_worked:new",
            {"day_worked": str(day_worked.id)}
        )

    return DayWorked.serialize(day_worked)


def get_day_worked(person_id, year, month, day):
    """
    Returns day worked for given day.
    """
    date = datetime.date(int(year), int(month), int(day))
    query = (
        DayWorked.query
        .filter(DayWorked.date == date.strftime("%Y-%m-%d"))
    )
    query = query.filter(DayWorked.person_id == person_id)

    day_worked = query.first()
    return DayWorked.serialize(day_worked) if day_worked else None


def get_days_worked(person_id):
    """
    Return all days worked for a given person.
    """
    query = (
        DayWorked.query
        .filter(DayWorked.person_id == person_id)
    )

    return DayWorked.serialize_list(query.all())


def get_month_days_worked(person_id, year, month):
    """
    Returns days worked for given person and month.
    """
    year = int(year)
    month = int(month)
    if (
        year < 2010
        or month < 1
        or month > 12
    ):
        raise WrongDateFormatException

    date = datetime.datetime(year, month, 1)
    next_month = date + relativedelta.relativedelta(months=1)

    query = DayWorked.query
    for day_worked_filter in (
        DayWorked.person_id == person_id,
        DayWorked.date >= date.strftime("%Y-%m-%d"),
        DayWorked.date < next_month.strftime("%Y-%m-%d")
    ):
        query = query.filter(day_worked_filter)

    return DayWorked.serialize_list(query.all())


def get_work_location(work_location_id):
    """
    Get work location data from a given id.

    :return: Serialized work location data
    :rtype: dict
    """
    work_location = WorkLocation.get(work_location_id)
    return work_location.serialize()


def get_or_create_work_location(name):
    """
    Create a new work location if it doesn't exist.
    If it exists, it returns the location from database.

    :return: Serialized work location data
    :rtype: dict
    """
    return get_or_create_instance_by_name(WorkLocation, name=name)
