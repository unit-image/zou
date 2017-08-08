import unittest
import json
import os
import ntpath
import shutil

from mixer.backend.flask import mixer

from zou.app import app
from zou.app.utils import fields, auth, fs
from zou.app.project import file_tree

from zou.app.models.project import Project
from zou.app.models.person import Person
from zou.app.models.department import Department
from zou.app.models.working_file import WorkingFile
from zou.app.models.output_file import OutputFile
from zou.app.models.output_type import OutputType
from zou.app.models.project_status import ProjectStatus
from zou.app.models.entity import Entity
from zou.app.models.entity_type import EntityType
from zou.app.models.task import Task
from zou.app.models.task_type import TaskType
from zou.app.models.task_status import TaskStatus
from zou.app.models.file_status import FileStatus


class ApiTestCase(unittest.TestCase):
    """
    Set of helpers to make test development easier.
    """

    def setUp(self):
        """
        Configure Flask application before each test.
        """
        app.test_request_context(headers={
            "mimetype": "application/json"
        })
        self.flask_app = app
        self.app = app.test_client()
        self.base_headers = {}
        self.post_headers = {"Content-type": "application/json"}
        try:
            shutil.rmtree(self.flask_app.config["JWT_TOKEN_FOLDER"])
        except OSError:
            pass
        fs.mkdir_p(self.flask_app.config["JWT_TOKEN_FOLDER"])

    def log_in(self, email):
        tokens = self.post("auth/login", {
            "email": email,
            "password": "mypassword"
        }, 200)
        self.auth_headers = {
            "Authorization": "Bearer %s" % tokens["access_token"]
        }
        self.base_headers.update(self.auth_headers)
        self.post_headers.update(self.auth_headers)

    def get(self, path, code=200):
        """
        Get data provided at given path. Format depends on the path.
        """
        response = self.app.get(path, headers=self.base_headers)
        self.assertEqual(response.status_code, code)
        return json.loads(response.data.decode("utf-8"))

    def get_raw(self, path, code=200):
        """
        Get data provided at given path. Format depends on the path. Do not
        parse the json.
        """
        response = self.app.get(path, headers=self.base_headers)
        self.assertEqual(response.status_code, code)
        return response.data.decode("utf-8")

    def get_first(self, path, code=200):
        """
        Get first element of data at given path. It makes the assumption that
        returned data is an array.
        """
        rows = self.get(path, code)
        return rows[0]

    def get_404(self, path):
        """
        Make sure that given path returns a 404 error for GET requests.
        """
        response = self.app.get(path, headers=self.base_headers)
        self.assertEqual(response.status_code, 404)

    def post(self, path, data, code=201):
        """
        Run a post request at given path while making sure it sends data at JSON
        format.
        """
        clean_data = fields.serialize_value(data)
        response = self.app.post(
            path,
            data=json.dumps(clean_data),
            headers=self.post_headers
        )
        self.assertEqual(response.status_code, code)
        return json.loads(response.data.decode("utf-8"))

    def post_404(self, path, data):
        """
        Make sure that given path returns a 404 error for POST requests.
        """
        response = self.app.post(
            path,
            data=json.dumps(data),
            headers=self.post_headers
        )
        self.assertEqual(response.status_code, 404)

    def put(self, path, data, code=200):
        """
        Run a put request at given path while making sure it sends data at JSON
        format.
        """
        response = self.app.put(
            path,
            data=json.dumps(data),
            headers=self.post_headers
        )
        self.assertEqual(response.status_code, code)
        return json.loads(response.data.decode("utf-8"))

    def put_404(self, path, data):
        """
        Make sure that given path returns a 404 error for PUT requests.
        """
        response = self.app.put(
            path,
            data=json.dumps(data),
            headers=self.post_headers
        )
        self.assertEqual(response.status_code, 404)

    def delete(self, path, code=204):
        """
        Run a delete request at given path.
        """
        response = self.app.delete(path, headers=self.base_headers)
        self.assertEqual(response.status_code, code)
        return response.data

    def delete_404(self, path):
        """
        Make sure that given path returns a 404 error for DELETE requests.
        """
        response = self.app.get(path, headers=self.base_headers)
        self.assertEqual(response.status_code, 404)

    def upload_file(self, path, file_path, code=201):
        """
        Upload a file at given path. File data are sent in the request body.
        """
        file_content = open(file_path, "rb")
        file_name = ntpath.basename(file_path)
        response = self.app.post(
            path,
            data={"file": (file_content, file_name)},
            headers=self.base_headers
        )
        self.assertEqual(response.status_code, code)
        return response.data

    def download_file(self, path, target_file_path, code=200):
        """
        Download a file located at given url path and save it at given file
        path.
        """
        response = self.app.get(path, headers=self.base_headers)
        self.assertEqual(response.status_code, code)
        file_descriptor = open(target_file_path, "wb")
        file_descriptor.write(response.data)
        return open(target_file_path, "rb").read()

    def tearDown(self):
        try:
            shutil.rmtree(self.flask_app.config["JWT_TOKEN_FOLDER"])
        except OSError:
            pass


class ApiDBTestCase(ApiTestCase):

    def setUp(self):
        """
        Reset database before each test.
        """
        super(ApiDBTestCase, self).setUp()

        from zou.app.utils import dbhelpers
        dbhelpers.drop_all()
        dbhelpers.create_all()
        self.generate_fixture_user()
        self.log_in(self.user.email)

    def tearDown(self):
        """
        Delete database after each test.
        """
        from zou.app.utils import dbhelpers
        dbhelpers.drop_all()

    def generate_data(self, cls, number, **kwargs):
        """
        Generate random data for a given data model.
        """
        mixer.init_app(self.flask_app)
        return mixer.cycle(number).blend(
            cls,
            id=fields.gen_uuid,
            **kwargs
        )

    def generate_fixture_project_status(self):
        self.open_status = ProjectStatus(name="open", color="#FFFFFF")
        self.open_status.save()

    def generate_fixture_project_closed_status(self):
        self.closed_status = ProjectStatus(name="closed", color="#FFFFFF")
        self.closed_status.save()

    def generate_fixture_project(self):
        self.project = Project(
            name="Cosmos Landromat",
            project_status_id=self.open_status.id
        )
        self.project.save()
        self.project.update({
            "file_tree": file_tree.get_tree_from_file("simple")
        })

    def generate_fixture_project_closed(self):
        self.project_closed = Project(
            name="Old Project",
            project_status_id=self.closed_status.id
        )
        self.project_closed.save()

    def generate_fixture_project_standard(self):
        self.project_standard = Project(
            name="Big Buck Bunny",
            project_status_id=self.open_status.id
        )
        self.project_standard.save()
        self.project_standard.update({
            "file_tree": file_tree.get_tree_from_file("standard")
        })

    def generate_fixture_project_no_preview_tree(self):
        self.project_no_preview_tree = Project(
            name="Agent 327",
            project_status_id=self.open_status.id
        )
        self.project_no_preview_tree.save()
        self.project_no_preview_tree.update({
            "file_tree": file_tree.get_tree_from_file("no_preview")
        })

    def generate_fixture_entity(self):
        self.entity = Entity(
            name="Tree",
            description="Description Tree",
            project_id=self.project.id,
            entity_type_id=self.entity_type.id
        )
        self.entity.save()

    def generate_fixture_entity_standard(self):
        self.entity_standard = Entity(
            name="Car",
            project_id=self.project_standard.id,
            entity_type_id=self.entity_type.id
        )
        self.entity_standard.save()

    def generate_fixture_sequence(self):
        if hasattr(self, "episode"):
            episode_id = self.episode.id
        else:
            episode_id = None

        self.sequence = Entity(
            name="S01",
            project_id=self.project.id,
            entity_type_id=self.sequence_type.id,
            parent_id=episode_id
        )
        self.sequence.save()

    def generate_fixture_sequence_standard(self):
        self.sequence_standard = Entity(
            name="S01",
            project_id=self.project_standard.id,
            entity_type_id=self.sequence_type.id
        )
        self.sequence_standard.save()

    def generate_fixture_episode(self):
        self.episode = Entity(
            name="E01",
            project_id=self.project.id,
            entity_type_id=self.episode_type.id
        )
        self.episode.save()

    def generate_fixture_shot(self):
        self.shot = Entity(
            name="P01",
            description="Description Shot 01",
            data={
                "fps": 25,
                "frame_in": 0,
                "frame_out": 100
            },
            project_id=self.project.id,
            entity_type_id=self.shot_type.id,
            parent_id=self.sequence.id
        )
        self.shot.save()
        self.shot_noseq = Entity(
            name="P01NOSEQ",
            project_id=self.project.id,
            entity_type_id=self.shot_type.id
        )
        self.shot_noseq.save()

    def generate_fixture_shot_standard(self):
        self.shot_standard = Entity(
            name="P01",
            description="Description Shot 01",
            data={
                "fps": 25,
                "frame_in": 0,
                "frame_out": 100
            },
            project_id=self.project_standard.id,
            entity_type_id=self.shot_type.id,
            parent_id=self.sequence_standard.id
        )
        self.shot_standard.save()

    def generate_fixture_user(self):
        self.user = Person(
            first_name="John",
            last_name="Did",
            email=u"john.did@gmail.com",
            password=auth.encrypt_password("mypassword")
        )
        self.user.save()

    def generate_fixture_person(self):
        self.person = Person(
            first_name="John",
            last_name="Doe",
            email=u"john.doe@gmail.com",
            password=auth.encrypt_password("mypassword")
        )
        self.person.save()

    def generate_fixture_entity_type(self):
        self.entity_type = EntityType(name="Props")
        self.entity_type.save()
        self.shot_type = EntityType(name="Shot")
        self.shot_type.save()
        self.sequence_type = EntityType(name="Sequence")
        self.sequence_type.save()
        self.episode_type = EntityType(name="Episode")
        self.episode_type.save()

    def generate_fixture_department(self):
        self.department = Department(name="Modeling", color="#FFFFFF")
        self.department.save()
        self.department_animation = Department(
            name="Animation",
            color="#FFFFFF"
        )
        self.department_animation.save()

    def generate_fixture_task_type(self):
        self.task_type = TaskType(
            name="Shaders",
            color="#FFFFFF",
            department_id=self.department.id
        )
        self.task_type.save()
        self.task_type_animation = TaskType(
            name="Animation",
            color="#FFFFFF",
            department_id=self.department_animation.id
        )
        self.task_type_animation.save()

    def generate_fixture_task_status(self):
        self.task_status = TaskStatus(
            name="Open",
            short_name="opn",
            color="#FFFFFF"
        )
        self.task_status.save()

    def generate_fixture_task_status_wip(self):
        self.task_status_wip = TaskStatus(
            name="WIP",
            short_name="wip",
            color="#FFFFFF"
        )
        self.task_status_wip.save()

    def generate_fixture_task_status_to_review(self):
        self.task_status_to_review = TaskStatus(
            name="To review",
            short_name="pndng",
            color="#FFFFFF"
        )
        self.task_status_to_review.save()

    def generate_fixture_assigner(self):
        self.assigner = Person(first_name="Ema", last_name="Peel")
        self.assigner.save()

    def generate_fixture_task(self, name="Master"):
        start_date = fields.get_date_object("2017-02-20")
        due_date = fields.get_date_object("2017-02-28")
        real_start_date = fields.get_date_object("2017-02-22")
        self.task = Task(
            name=name,
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

    def generate_fixture_task_standard(self):
        start_date = fields.get_date_object("2017-02-20")
        due_date = fields.get_date_object("2017-02-28")
        real_start_date = fields.get_date_object("2017-02-22")
        self.task_standard = Task(
            name="Super modeling",
            project_id=self.project_standard.id,
            task_type_id=self.task_type.id,
            task_status_id=self.task_status.id,
            entity_id=self.entity_standard.id,
            assignees=[self.person],
            assigner_id=self.assigner.id,
            duration=50,
            estimation=40,
            start_date=start_date,
            due_date=due_date,
            real_start_date=real_start_date
        )
        self.task_standard.save()

    def generate_fixture_shot_task(self, name="Master"):
        self.shot_task = Task(
            name=name,
            project_id=self.project.id,
            task_type_id=self.task_type_animation.id,
            task_status_id=self.task_status.id,
            entity_id=self.shot.id,
            assignees=[self.person],
            assigner_id=self.assigner.id,
        )
        self.shot_task.save()

    def generate_fixture_shot_task_standard(self):
        self.shot_task_standard = Task(
            name="Super animation",
            project_id=self.project_standard.id,
            task_type_id=self.task_type_animation.id,
            task_status_id=self.task_status.id,
            entity_id=self.shot_standard.id,
            assignees=[self.person],
            assigner_id=self.assigner.id
        )
        self.shot_task_standard.save()

    def generate_fixture_file_status(self):
        self.file_status = FileStatus(
            name="To review",
            color="#FFFFFF"
        )
        self.file_status.save()

    def generate_fixture_working_file(self, name="main", revision=1):
        self.working_file = WorkingFile(
            name=name,
            comment="",
            revision=revision,
            task_id=self.task.id,
            entity_id=self.entity.id,
            person_id=self.person.id
        )
        self.working_file.save()
        return self.working_file

    def generate_fixture_shot_working_file(self):
        self.working_file = WorkingFile(
            name="main",
            comment="",
            revision=1,
            task_id=self.shot_task.id,
            entity_id=self.shot.id,
            person_id=self.person.id
        )
        self.working_file.save()

    def generate_fixture_output_file(self):
        self.output_file = OutputFile.create(
            comment="",
            revision=1,
            task_id=self.task.id,
            entity_id=self.entity.id,
            person_id=self.person.id,
            file_status_id=self.file_status.id,
            output_type_id=self.output_type.id
        )
        return self.output_file

    def generate_fixture_output_type(self):
        self.output_type = OutputType.create(
            name="Geometry",
            short_name="Geo"
        )

    def get_fixture_file_path(self, relative_path):
        current_path = os.getcwd()
        file_path_fixture = os.path.join(
            current_path,
            "test",
            "fixtures",
            relative_path
        )
        return file_path_fixture
