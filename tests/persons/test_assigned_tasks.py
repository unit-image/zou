
from tests.base import ApiDBTestCase
from zou.app import db
from zou.app.utils import fields


class PersonAssignedTasksTestCase(ApiDBTestCase):

    def setUp(self):
        super(PersonAssignedTasksTestCase, self).setUp()
        self.generate_fixture_person()

        self.generate_fixture_department()
        self.generate_fixture_task_type()
        self.generate_fixture_task_status()
        self.generate_fixture_asset_type()
        self.generate_fixture_assigner()

        # --- Active Project ---

        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_asset()

        self.active_task = self.generate_fixture_task(name="ActiveTask")

        # --- Old Task ---

        self.old_task = self.generate_fixture_task(name="OldTask", task_type_id=self.task_type_animation.id)
        self.old_task.updated_at = fields.get_date_object("2017-02-20")
        db.session.add(self.old_task)
        db.session.commit()

        # --- Closed Project ---

        self.generate_fixture_project_closed_status()
        self.generate_fixture_project_closed()
        self.project = self.project_closed
        self.generate_fixture_asset()

        self.generate_fixture_task(name="ClosedTask")

        # Storing the person_id because the Person object is not bound to a
        # session and throws a DetachedInstanceError when the id is accessed
        # later.
        self.person_id = str(self.person.id)

    def test_get_assigned_tasks(self):
        assigned_tasks = self.get(
            "/data/persons/%s/assigned-tasks" % self.person_id
        )

        assert len(assigned_tasks) == 2
        assert assigned_tasks[0]["id"] == str(self.active_task.id)
        assert assigned_tasks[1]["id"] == str(self.old_task.id)

    def test_get_max_update_age_assigned_tasks(self):
        assigned_tasks = self.get(
            "/data/persons/%s/assigned-tasks?max_update_age=60" % self.person_id
        )

        assert len(assigned_tasks) == 1
        assert assigned_tasks[0]["id"] == str(self.active_task.id)
