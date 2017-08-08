from test.base import ApiDBTestCase

from zou.app.utils import events

from zou.app.project import file_info


class PublishFileTestCase(ApiDBTestCase):

    def setUp(self):
        super(PublishFileTestCase, self).setUp()

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
        self.generate_fixture_person()
        self.generate_fixture_assigner()
        self.generate_fixture_task()
        self.generate_fixture_shot_task()
        self.generate_fixture_working_file()
        self.generate_fixture_shot_working_file()
        self.tx_type_id = str(
            file_info.get_or_create_output_type("tx").id
        )
        self.cache_type_id = str(
            file_info.get_or_create_output_type("Cache").id
        )
        self.person_id = self.person.id
        self.working_file_id = str(self.working_file.id)

        events.unregister_all()

    def publish(self, publish_data, code=201):
        path = "project/tasks/%s/working-files/%s/publish" % (
            self.task.id,
            self.working_file_id
        )
        result = self.post(
            path,
            publish_data,
            code
        )
        return result

    def test_publish(self):
        publish_data = {
            "person_id": self.person_id,
            "comment": "test working file publish",
            "output_type_id": self.tx_type_id
        }
        result = self.publish(publish_data)

        self.assertEqual(
            result["folder_path"],
            "/simple/productions/export/cosmos_landromat/assets/props/tree/"
            "shaders/tx"
        )
        self.assertEqual(
            result["file_name"],
            "cosmos_landromat_props_tree_shaders_tx_v001"
        )

        output_file_id = result["id"]
        output_file = self.get("data/output_files/%s" % output_file_id)

        self.assertEqual(output_file["comment"], publish_data["comment"])
        self.assertEqual(output_file["revision"], 1)
        self.assertEqual(output_file["source_file_id"], self.working_file_id)

        self.assertEqual(
            result["preview_path"]["folder_path"],
            "/simple/productions/previews/cosmos_landromat/assets/props/tree/"
            "shaders"
        )
        self.assertEqual(
            result["preview_path"]["file_name"],
            "cosmos_landromat_props_tree_shaders_v001"
        )

    def test_publish_no_preview(self):
        self.generate_fixture_project_no_preview_tree()
        self.entity.update({"project_id": self.project_no_preview_tree.id})
        self.task.update({"project_id": self.project_no_preview_tree.id})
        publish_data = {
            "task_id": self.task.id,
            "person_id": self.person.id,
            "comment": "test working file publish",
            "output_type_id": self.tx_type_id
        }
        result = self.publish(publish_data)

        self.assertEqual(
            result["folder_path"],
            "/simple/productions/export/agent_327/assets/props/tree/"
            "shaders/tx"
        )
        self.assertEqual(
            result["file_name"],
            "agent_327_props_tree_shaders_tx_v001"
        )
        self.assertEqual(len(result["preview_path"]["folder_path"]), 0)
        self.assertEqual(len(result["preview_path"]["file_name"]), 0)

    def test_publish_wrong_data(self):
        publish_data = {
            "comment_wrong": "test file publish"
        }
        self.publish(publish_data, 400)

    def test_publish_new_revision(self):
        publish_data = {
            "task_id": self.task.id,
            "person_id": self.person.id,
            "working_file_id": self.working_file_id,
            "comment": "test working file publish"
        }

        self.post(
            "project/tasks/%s/working-files/%s/publish" % (
                self.task.id,
                self.working_file_id
            ),
            publish_data
        )
        result = self.post(
            "project/tasks/%s/working-files/%s/publish" % (
                self.task.id,
                self.working_file_id
            ),
            publish_data
        )
        output_file_id = result["id"]
        output_file = self.get("data/output_files/%s" % output_file_id)
        self.assertEqual(output_file["revision"], 2)
