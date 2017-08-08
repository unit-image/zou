# -*- coding: UTF-8 -*-
import datetime

from test.base import ApiDBTestCase

from zou.app.models.task import Task
from zou.app.models.task_type import TaskType
from zou.app.project import task_info
from zou.app.utils import events, fields

from zou.app.project.exception import TaskNotFoundException


class ToReviewHandler(object):

    def __init__(self, open_status_id, to_review_status_id):
        self.is_event_fired = False
        self.open_status_id = open_status_id
        self.to_review_status_id = to_review_status_id

    def handle_event(self, data):
        self.is_event_fired = True
        self.data = data


class TaskInfoTestCase(ApiDBTestCase):

    def setUp(self):
        super(TaskInfoTestCase, self).setUp()

        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_entity_type()
        self.generate_fixture_entity()
        self.generate_fixture_sequence()
        self.generate_fixture_shot()
        self.generate_fixture_department()
        self.generate_fixture_task_type()
        self.generate_fixture_task_status()
        self.generate_fixture_task_status_wip()
        self.generate_fixture_task_status_to_review()
        self.generate_fixture_person()
        self.generate_fixture_assigner()
        self.generate_fixture_task()
        self.generate_fixture_shot_task()
        self.generate_fixture_file_status()
        self.generate_fixture_working_file()
        self.generate_fixture_output_type()
        self.generate_fixture_output_file()

        self.task_id = self.task.id
        self.open_status_id = self.task_status.id
        self.wip_status_id = self.task_status_wip.id
        self.to_review_status_id = self.task_status_to_review.id

        self.is_event_fired = False
        events.unregister_all()

    def handle_event(self, data):
        self.is_event_fired = True
        self.assertEqual(
            data["task_before"]["task_status_id"],
            str(self.open_status_id)
        )
        self.assertEqual(
            data["task_after"]["task_status_id"],
            str(self.wip_status_id)
        )

    def assert_event_is_fired(self):
        self.assertTrue(self.is_event_fired)

    def test_get_status(self):
        task_status = task_info.get_or_create_status("WIP", "wip")
        self.assertEqual(task_status.name, "WIP")

    def test_get_wip_status(self):
        task_status = task_info.get_wip_status()
        self.assertEqual(task_status.name, "WIP")

    def test_get_todo_status(self):
        task_status = task_info.get_todo_status()
        self.assertEqual(task_status.name, "Todo")

    def test_get_to_review_status(self):
        task_status = task_info.get_to_review_status()
        self.assertEqual(task_status.name, "To review")

    def test_create_task(self):
        shot = self.shot.serialize()
        task_type = self.task_type.serialize()
        status = task_info.get_todo_status().serialize()
        task = task_info.create_task(task_type, shot)
        task = task_info.get_task(task["id"]).serialize()
        self.assertEquals(task["entity_id"], shot["id"])
        self.assertEquals(task["task_type_id"], task_type["id"])
        self.assertEquals(task["project_id"], shot["project_id"])
        self.assertEquals(task["task_status_id"], status["id"])

    def test_status_to_wip(self):
        events.register(
            "task:start",
            "mark_event_as_fired",
            self
        )

        now = datetime.datetime.now()
        self.task.update({"real_start_date": None})
        task_info.start_task(self.task)

        task = Task.get(self.task.id)
        self.assertEqual(task.task_status_id, self.wip_status_id)
        self.assertGreater(task.real_start_date.isoformat(), now.isoformat())
        self.assert_event_is_fired()

    def test_status_to_wip_twice(self):
        task_info.start_task(self.task)
        task = Task.get(self.task.id)
        real_start_date = task.real_start_date
        task.update({
            "task_status_id": self.task_status.id
        })

        task_info.start_task(self.task)
        task = Task.get(self.task.id)
        self.assertEqual(task.real_start_date, real_start_date)

    def test_publish_task(self):
        handler = ToReviewHandler(self.open_status_id, self.to_review_status_id)
        events.register(
            "task:to-review",
            "mark_event_as_fired",
            handler
        )
        task_info.to_review_task(self.task, self.output_file.serialize())
        self.is_event_fired = handler.is_event_fired
        data = handler.data

        task = Task.get(self.task.id)
        self.assertEqual(task.task_status_id, self.to_review_status_id)
        self.assert_event_is_fired()

        self.assertEquals(
            data["task_before"]["task_status_id"],
            str(self.open_status_id)
        )

        self.assertEquals(
            data["task_after"]["task_status_id"],
            str(self.to_review_status_id)
        )

        self.assertEquals(
            data["task_after"]["project"]["id"],
            str(self.project.id)
        )

        self.assertEquals(
            data["task_after"]["entity"]["id"],
            str(self.entity.id)
        )

        self.assertEquals(
            data["task_after"]["entity_type"]["id"],
            str(self.entity_type.id)
        )

        self.assertEquals(
            data["task_after"]["person"]["id"],
            str(self.person.id)
        )

        self.assertEquals(
            data["task_after"]["output_file"]["id"],
            str(self.output_file.id)
        )

    def test_assign_task(self):
        task_info.assign_task(self.task, self.assigner)
        self.assertEqual(self.task.assignees[1].id, self.assigner.id)

    def test_get_department_from_task_type(self):
        department = task_info.get_department_from_task_type(self.task_type)
        self.assertEqual(department.name, "Modeling")

    def test_get_task(self):
        self.assertRaises(
            TaskNotFoundException,
            task_info.get_task,
            "wrong-id"
        )
        task = task_info.get_task(self.task_id)
        self.assertEqual(self.task_id, task.id)
        self.output_file.delete()
        self.working_file.delete()
        task.delete()

        self.assertRaises(
            TaskNotFoundException,
            task_info.get_task,
            self.task_id
        )

    def test_get_task_dicts_for_shot(self):
        tasks = task_info.get_task_dicts_for_shot(self.shot.id)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], str(self.shot_task.id))

    def test_get_task_dicts_for_asset(self):
        tasks = task_info.get_task_dicts_for_asset(self.entity.id)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], str(self.task.id))

    def test_get_task_dicts_for_entity(self):
        tasks = task_info.get_task_dicts_for_entity(self.entity.id)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], str(self.task.id))
        self.assertEqual(tasks[0]["task_type_name"], str("Shaders"))
        self.assertEqual(tasks[0]["entity_name"], str("Tree"))

    def test_get_task_dicts_for_entity_utf8(self):
        start_date = fields.get_date_object("2017-02-20")
        due_date = fields.get_date_object("2017-02-28")
        real_start_date = fields.get_date_object("2017-02-22")
        self.working_file.delete()
        self.output_file.delete()
        self.task.delete()
        self.task_type = TaskType(
            name="Modélisation",
            color="#FFFFFF",
            department_id=self.department.id
        )
        self.task_type.save()
        self.task = Task(
            name="Première Tâche",
            project_id=self.project.id,
            task_type_id=self.task_type.id,
            task_status_id=self.task_status.id,
            entity_id=self.entity.id,
            assignees=[self.person],
            assigner_id=self.assigner.id,
            duration=50,
            estimation=40,
            start_date=start_date,
            due_date=due_date,
            real_start_date=real_start_date
        )
        self.task.save()

        tasks = task_info.get_task_dicts_for_entity(self.entity.id)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["name"], u"Première Tâche")
        self.assertEqual(tasks[0]["task_type_name"], u"Modélisation")
