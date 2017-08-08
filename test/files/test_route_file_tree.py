from test.base import ApiDBTestCase

from zou.app.project import file_info


class FolderPathTestCase(ApiDBTestCase):

    def setUp(self):
        super(FolderPathTestCase, self).setUp()

        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_person()
        self.generate_fixture_assigner()
        self.generate_fixture_entity_type()
        self.generate_fixture_entity()
        self.generate_fixture_sequence()
        self.generate_fixture_shot()
        self.generate_fixture_department()
        self.generate_fixture_task_type()
        self.generate_fixture_task_status()
        self.generate_fixture_shot_task()
        self.generate_fixture_task()
        self.cache_type_id = str(
            file_info.get_or_create_output_type("Cache").id
        )
        self.render_type_id = str(
            file_info.get_or_create_output_type("Render").id
        )

    def test_get_path_shot(self):
        data = {
            "mode": "working",
            "task_id": self.shot_task.id
        }
        result = self.post("project/tree/folder", data, 200)
        self.assertEquals(
            result["path"],
            "/simple/productions/cosmos_landromat/shots/s01/p01/animation/"
            "3dsmax"
        )

    def test_get_file_path_asset(self):
        self.generate_fixture_working_file("hotfix", revision=1)
        self.generate_fixture_working_file("hotfix", revision=2)
        self.generate_fixture_working_file("hotfix", revision=3)
        self.generate_fixture_working_file("hotfix", revision=4)

        task_id = str(self.task.id)
        data = {
            "mode": "working",
            "name": "main",
            "task_id": task_id
        }
        result = self.post("project/tree/file", data, 200)
        self.assertEquals(
            result["path"],
            "/simple/productions/cosmos_landromat/assets/props/tree/shaders/"
            "3dsmax"
        )
        self.assertEquals(
            result["name"],
            "cosmos_landromat_props_tree_shaders_main_v001"
        )

        data = {
            "mode": "working",
            "name": "hotfix",
            "task_id": task_id
        }
        result = self.post("project/tree/file", data, 200)
        self.assertEquals(
            result["name"],
            "cosmos_landromat_props_tree_shaders_hotfix_v005"
        )

        data = {
            "mode": "working",
            "name": "hotfix",
            "task_id": task_id,
            "version": 3
        }
        result = self.post("project/tree/file", data, 200)
        self.assertEquals(
            result["name"],
            "cosmos_landromat_props_tree_shaders_hotfix_v003"
        )

    def test_get_path_shot_output(self):
        data = {
            "mode": "output",
            "output_type_id": self.cache_type_id,
            "task_id": self.shot_task.id
        }
        result = self.post("project/tree/folder", data, 200)
        self.assertEquals(
            result["path"],
            "/simple/productions/export/cosmos_landromat/shots/s01/p01/"
            "animation/cache"
        )

    def test_get_path_asset(self):
        data = {
            "mode": "working",
            "task_id": self.task.id
        }
        result = self.post("project/tree/folder", data, 200)
        self.assertEquals(
            result["path"],
            "/simple/productions/cosmos_landromat/assets/props/tree/"
            "shaders/3dsmax"
        )

    def test_get_path_asset_software(self):
        data = {
            "mode": "working",
            "software": "maya",
            "task_id": self.task.id
        }
        result = self.post("project/tree/folder", data, 200)
        self.assertEquals(
            result["path"],
            "/simple/productions/cosmos_landromat/assets/props/tree/shaders/"
            "maya"
        )

    def test_get_path_asset_outputtype(self):
        data = {
            "mode": "output",
            "output_type_id": self.render_type_id,
            "task_id": self.task.id
        }
        result = self.post("project/tree/folder", data, 200)
        self.assertEquals(
            result["path"],
            "/simple/productions/export/cosmos_landromat/assets/props/tree/"
            "shaders/render"
        )

    def test_get_file_path_asset_outputtype(self):
        data = {
            "mode": "output",
            "output_type_id": self.render_type_id,
            "task_id": self.task.id
        }
        result = self.post("project/tree/file", data, 200)
        self.assertEquals(
            result["path"],
            "/simple/productions/export/cosmos_landromat/assets/props/tree/"
            "shaders/render"
        )

    def test_get_path_asset_wrong_data(self):
        data = {
            "task_type_id": self.task_type.id,
            "asset_id": self.entity.id,
        }
        self.post("project/tree/folder", data, 400)

    def test_get_file_path_asset_with_version(self):
        data = {
            "mode": "working",
            "task_id": self.task.id,
            "version": 3
        }
        result = self.post("project/tree/file", data, 200)
        self.assertEquals(
            result["path"],
            "/simple/productions/cosmos_landromat/assets/props/tree/shaders/"
            "3dsmax"
        )
        self.assertEquals(
            result["name"],
            "cosmos_landromat_props_tree_shaders_v003"
        )

    def test_get_folder_separator(self):
        data = {
            "mode": "working",
            "task_id": self.task.id,
            "sep": "\\"
        }
        result = self.post("project/tree/folder", data, 200)
        self.assertEquals(
            result["path"],
            "/simple\\productions\\cosmos_landromat\\assets\\props\\tree\\"
            "shaders\\3dsmax"
        )

    def test_get_file_separator(self):
        data = {
            "mode": "working",
            "task_id": self.task.id,
            "sep": "\\"
        }
        result = self.post("project/tree/file", data, 200)
        self.assertEquals(
            result["path"],
            "/simple\\productions\\cosmos_landromat\\assets\\props\\tree\\"
            "shaders\\3dsmax"
        )

    def test_get_path_wrong_task_id(self):
        data = {
            "mode": "working",
            "task_id": self.task_type.id
        }
        self.post("project/tree/folder", data, 400)

    def test_get_name_wrong_task_id(self):
        data = {
            "mode": "working",
            "task_id": self.task_type.id
        }
        self.post("project/tree/file", data, 400)

    def test_get_path_wrong_mode(self):
        data = {
            "mode": "unknown",
            "task_id": self.task.id
        }
        self.post("project/tree/folder", data, 400)
