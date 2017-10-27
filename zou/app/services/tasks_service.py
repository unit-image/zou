import datetime

from sqlalchemy.exc import StatementError, IntegrityError, DataError

from zou.app import app
from zou.app.utils import events

from zou.app.models.comment import Comment
from zou.app.models.person import Person
from zou.app.models.task import Task
from zou.app.models.task_type import TaskType
from zou.app.models.department import Department
from zou.app.models.entity import Entity
from zou.app.models.task_status import TaskStatus
from zou.app.models.time_spent import TimeSpent
from zou.app.models.project import Project
from zou.app.models.entity_type import EntityType
from zou.app.models.preview_file import PreviewFile

from zou.app.services.exception import (
    CommentNotFoundException,
    TaskNotFoundException,
    TaskStatusNotFoundException,
    TaskTypeNotFoundException,
    WrongDateFormatException
)

from zou.app.services import (
    shots_service,
    assets_service,
    persons_service
)


def get_wip_status():
    return get_or_create_status(app.config["WIP_TASK_STATUS"], "wip")


def get_to_review_status():
    return get_or_create_status(app.config["TO_REVIEW_TASK_STATUS"], "pndng")


def get_todo_status():
    return get_or_create_status("Todo")


def get_task_status(task_status_id):
    try:
        task_status = TaskStatus.get(task_status_id)
    except StatementError:
        raise TaskStatusNotFoundException()

    if task_status is None:
        raise TaskStatusNotFoundException()
    return task_status


def start_task(task):
    wip_status = get_wip_status()
    task_is_not_already_wip = \
        task.task_status_id is None \
        or task.task_status_id != wip_status.id

    if task_is_not_already_wip:
        task_dict_before = task.serialize()

        new_data = {"task_status_id": wip_status.id}
        if task.real_start_date is None:
            new_data["real_start_date"] = datetime.datetime.now()

        task.update(new_data)

        task_dict_after = task.serialize()
        events.emit("task:start", {
            "task_before": task_dict_before,
            "task_after": task_dict_after
        })

    return task


def task_to_review(task, person, comment, preview_path=""):
    to_review_status = get_to_review_status()
    task_dict_before = task.serialize()

    task.update({"task_status_id": to_review_status.id})
    task.save()

    project = Project.get(task.project_id)
    entity = Entity.get(task.entity_id)
    entity_type = EntityType.get(entity.entity_type_id)

    task_dict_after = task.serialize()
    task_dict_after["project"] = project.serialize()
    task_dict_after["entity"] = entity.serialize()
    task_dict_after["entity_type"] = entity_type.serialize()
    task_dict_after["person"] = person.serialize()
    task_dict_after["comment"] = comment
    task_dict_after["preview_path"] = preview_path

    events.emit("task:to-review", {
        "task_before": task_dict_before,
        "task_after": task_dict_after
    })

    return task_dict_after


def get_task(task_id):
    try:
        task = Task.get(task_id)
    except StatementError:
        raise TaskNotFoundException()

    if task is None:
        raise TaskNotFoundException()

    return task


def get_task_type(task_type_id):
    try:
        task_type = TaskType.get(task_type_id)
    except StatementError:
        raise TaskTypeNotFoundException()

    if task_type is None:
        raise TaskTypeNotFoundException()

    return task_type.serialize()


def create_task(task_type, entity, name="main"):
    task_status = get_todo_status()
    try:
        try:
            current_user_id = persons_service.get_current_user().id
        except RuntimeError:
            current_user_id = None
        task = Task.create(
            name=name,
            duration=0,
            estimation=0,
            completion_rate=0,
            start_date=None,
            end_date=None,
            due_date=None,
            real_start_date=None,
            project_id=entity["project_id"],
            task_type_id=task_type["id"],
            task_status_id=task_status.id,
            entity_id=entity["id"],
            assigner_id=current_user_id,
            assignees=[]
        )
        return task.serialize()
    except IntegrityError:
        pass  # Tasks already exists, no need to create it.


def delete_task(task):
    task.delete()


def remove_task(task_id):
    task = Task.get(task_id)
    task.delete()


def assign_task(task, person):
    task.assignees.append(person)
    task.save()
    return task


def get_department_from_task_type(task_type):
    return Department.get(task_type.department_id)


def get_tasks_for_shot(shot_id):
    shot = shots_service.get_shot(shot_id)
    return get_task_dicts_for_entity(shot.id)


def get_tasks_for_sequence(sequence_id):
    sequence = shots_service.get_sequence(sequence_id)
    return get_task_dicts_for_entity(sequence.id)


def get_tasks_for_asset(asset_id):
    asset = assets_service.get_asset(asset_id)
    return get_task_dicts_for_entity(asset.id)


def get_task_dicts_for_entity(entity_id):
    query = Task.query.order_by(Task.name)
    query = query.filter_by(entity_id=entity_id)
    query = query.join(Project)
    query = query.join(TaskType)
    query = query.join(Department)
    query = query.join(TaskStatus)
    query = query.join(Entity, Task.entity_id == Entity.id)
    query = query.join(EntityType)
    query = query.add_columns(Project.name)
    query = query.add_columns(Department.name)
    query = query.add_columns(TaskType.name)
    query = query.add_columns(TaskStatus.name)
    query = query.add_columns(EntityType.name)
    query = query.add_columns(Entity.name)
    query = query.order_by(
        Project.name,
        Department.name,
        TaskType.name,
        EntityType.name,
        Entity.name
    )
    results = []

    for entry in query.all():
        (
            task_object,
            project_name,
            department_name,
            task_type_name,
            task_status_name,
            entity_type_name,
            entity_name
        ) = entry

        task = task_object.serialize()
        task["project_name"] = project_name
        task["department_name"] = department_name
        task["task_type_name"] = task_type_name
        task["task_status_name"] = task_status_name
        task["entity_type_name"] = entity_type_name
        task["entity_name"] = entity_name
        results.append(task)
    return results


def get_or_create_task_type(
    department,
    name,
    color="#888888",
    priority=1,
    for_shots=False
):
    task_type = TaskType.get_by(name=name)
    if task_type is None:
        task_type = TaskType(
            name=name,
            department_id=department.id,
            color=color,
            priority=priority,
            for_shots=for_shots
        )
        task_type.save()
    return task_type


def get_or_create_status(name, short_name="", color="#f5f5f5"):
    status = TaskStatus.get_by(name=name)
    if status is None and len(short_name) > 0:
        status = TaskStatus.get_by(short_name=short_name)

    if status is None:
        status = TaskStatus.create(
            name=name,
            short_name=short_name or name.lower(),
            color=color
        )
    return status


def get_or_create_department(name):
    departmemt = Department.get_by(name=name)
    if departmemt is None:
        departmemt = Department(
            name=name,
            color="#000000"
        )
        departmemt.save()
    return departmemt


def get_next_preview_revision(task_id):
    preview_files = PreviewFile.query.filter_by(
        task_id=task_id
    ).order_by(
        PreviewFile.revision.desc()
    ).all()

    revision = 1
    if len(preview_files) > 0:
        revision = preview_files[0].revision + 1
    return revision


def get_task_types_for_shot(shot_id):
    return get_task_types_for_entity(shot_id)


def get_task_types_for_sequence(sequence_id):
    return get_task_types_for_entity(sequence_id)


def get_task_types_for_asset(asset_id):
    return get_task_types_for_entity(asset_id)


def get_task_types_for_entity(entity_id):
    task_types = TaskType.query \
        .join(Task, Entity) \
        .filter(Entity.id == entity_id) \
        .all()
    return TaskType.serialize_list(task_types)


def create_or_update_time_spent(task_id, person_id, date, duration, add=False):
    try:
        time_spent = TimeSpent.get_by(
            task_id=task_id,
            person_id=person_id,
            date=date
        )
    except DataError:
        raise WrongDateFormatException

    if time_spent is not None:
        if add:
            time_spent.update({"duration": time_spent.duration + duration})
        else:
            time_spent.update({"duration": duration})
    else:
        time_spent = TimeSpent.create(
            task_id=task_id,
            person_id=person_id,
            date=date,
            duration=duration
        )
    return time_spent.serialize()


def get_time_spents(task_id):
    result = {"total": 0}
    time_spents = TimeSpent.query.filter_by(task_id=task_id).all()
    for time_spent in time_spents:
        result[str(time_spent.person_id)] = time_spent.serialize()
        result["total"] += time_spent.duration
    return result


def get_comments(task):
    comments = []

    query = Comment.query.order_by(Comment.created_at.desc()) \
        .filter_by(object_id=task.id) \
        .join(Person, TaskStatus) \
        .add_columns(
            TaskStatus.name,
            TaskStatus.short_name,
            TaskStatus.color,
            Person.first_name,
            Person.last_name
        )

    for result in query.all():
        (
            comment,
            task_status_name,
            task_status_short_name,
            task_status_color,
            person_first_name,
            person_last_name
        ) = result

        comment_dict = comment.serialize()
        comment_dict["person"] = {
            "first_name": person_first_name,
            "last_name": person_last_name,
            "id": str(comment.person_id)
        }
        comment_dict["task_status"] = {
            "name": task_status_name,
            "short_name": task_status_short_name,
            "color": task_status_color,
            "id": str(comment.task_status_id)
        }

        if comment.preview_file_id is not None:
            preview = PreviewFile.get(comment.preview_file_id)
            comment_dict["preview"] = {
                "id": str(preview.id),
                "revision": preview.revision
            }
        comments.append(comment_dict)
    return comments


def get_entity(entity_id):
    return Entity.get(entity_id)


def get_entity_type(entity_type_id):
    return EntityType.get(entity_type_id)


def get_comment(comment_id):
    try:
        comment = Comment.get(comment_id)
    except StatementError:
        raise CommentNotFoundException()

    if comment is None:
        raise CommentNotFoundException()
    return comment


def create_comment(
    object_id,
    task_status_id,
    person_id,
    text,
    object_type="Task"
):
    return Comment.create(
        object_id=object_id,
        object_type=object_type,
        task_status_id=task_status_id,
        person_id=person_id,
        text=text
    )
