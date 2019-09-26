from zou.app.models.project import Project
from zou.app.models.entity import Entity
from zou.app.models.entity_type import EntityType
from zou.app.models.person import Person
from zou.app.models.project_status import ProjectStatus
from zou.app.services.exception import ProjectNotFoundException

from zou.app.utils import fields, events

from sqlalchemy.exc import StatementError


def open_projects(name=None):
    """
    Return all open projects. Allow to filter projects by name.
    """
    query = Project.query \
        .join(ProjectStatus) \
        .filter(ProjectStatus.name.in_(("Active", "open", "Open"))) \
        .order_by(Project.name)

    if name is not None:
        query = query.filter(Project.name == name)

    return get_projects_with_first_episode(query)


def get_projects_with_first_episode(query):
    """
    Helpers function to attach first episode name to curent project.
    """
    projects = []
    for project in query.all():
        project_dict = project.serialize()
        if project.production_type == "tvshow":
            first_episode = Entity.query \
                .join(EntityType) \
                .filter(EntityType.name == 'Episode') \
                .filter(Entity.project_id == project.id) \
                .order_by(Entity.name) \
                .first()
            if first_episode is not None:
                project_dict["first_episode_id"] = \
                    fields.serialize_value(first_episode.id)
        projects.append(project_dict)

    return projects


def get_projects():
    """
    Return all projects. Allow to filter projects by name.
    """
    query = Project.query \
        .join(ProjectStatus) \
        .add_columns(ProjectStatus.name) \
        .order_by(Project.name)

    result = []
    for entry in query.all():
        (project, project_status_name) = entry
        data = project.serialize()
        data["project_status_name"] = project_status_name
        result.append(data)

    return result


def get_or_create_open_status():
    """
    Return open status. If it does not exist, it creates it.
    """
    return get_or_create_status("Open")


def get_open_status():
    """
    Return open status. If it does not exist, it creates it.
    """
    get_or_create_status("Open")


def get_closed_status():
    """
    Return closed status. If it does not exist, it creates it.
    """
    get_or_create_status("Closed")


def get_or_create_status(name):
    """
    Return given status. If it does not exist, it creates it.
    """
    project_status = ProjectStatus.get_by(name=name)
    if project_status is None:
        project_status = ProjectStatus(
            name=name,
            color="#000000"
        )
        project_status.save()
    return project_status.serialize()


def save_project_status(project_statuses):
    """
    Save in database all project status given in parameter.
    """
    result = []
    filtered_satuses = (x for x in project_statuses if x is not None)

    for status in filtered_satuses:
        project_status = get_or_create_status(status)
        result.append(project_status)
    return result


def get_or_create_project(name):
    """
    Get project which match given name. Create it if it does not exist.
    """
    project = Project.get_by(name=name)
    if project is None:
        open_status = get_or_create_open_status()
        project = Project(
            name=name,
            project_status_id=open_status["id"]
        )
        project.save()
    return project.serialize()


def get_project_raw(project_id):
    """
    Get project matching given id, as active record. Raises an exception if
    project is not found.
    """
    try:
        project = Project.get(project_id)
    except StatementError:
        raise ProjectNotFoundException()

    if project is None:
        raise ProjectNotFoundException()

    return project


def get_project(project_id):
    """
    Get project matching given id, as a dict. Raises an exception if project is
    not found.
    """
    return get_project_raw(project_id).serialize()


def get_project_by_name(project_name):
    """
    Get project matching given name. Raises an exception if project is not
    found.
    """
    project = Project.query.filter(Project.name.ilike(project_name)).first()

    if project is None:
        raise ProjectNotFoundException()

    return project.serialize()


def update_project(project_id, data):
    """
    Update project matching given id with data from *data* dict.
    """
    project = get_project_raw(project_id)
    project.update(data)
    events.emit("project:update", {
        "project_id": project_id
    })
    return project.serialize()


def add_team_member(project_id, person_id):
    """
    Add a a person listed in database to the the project team.
    """
    project = get_project_raw(project_id)
    person = Person.get(person_id)
    project.team.append(person)
    project.save()
    return project.serialize()


def remove_team_member(project_id, person_id):
    """
    Remove a a person listed in database from the the project team.
    """
    project = get_project_raw(project_id)
    person = Person.get(person_id)
    project.team.remove(person)
    project.save()
    return project.serialize()
