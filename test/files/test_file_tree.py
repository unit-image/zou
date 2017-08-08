from test.base import ApiDBTestCase

from zou.app.project import file_tree

from zou.app.models.entity import Entity

from zou.app.project.exception import MalformedFileTreeException

from zou.app.project import file_info


class FileTreeTestCase(ApiDBTestCase):

    def setUp(self):
        super(FileTreeTestCase, self).setUp()
        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_project_standard()
        self.generate_fixture_entity_type()
        self.generate_fixture_entity()
        self.generate_fixture_episode()
        self.generate_fixture_sequence()
        self.generate_fixture_shot()
        self.generate_fixture_sequence_standard()
        self.generate_fixture_shot_standard()
        self.generate_fixture_person()
        self.generate_fixture_department()
        self.generate_fixture_task_type()
        self.generate_fixture_task_status()
        self.generate_fixture_assigner()
        self.generate_fixture_task()
        self.generate_fixture_shot_task()
        self.generate_fixture_shot_task_standard()
        self.entity_standard = Entity(
            name='Car',
            project_id=self.project_standard.id,
            entity_type_id=self.entity_type.id
        )
        self.entity_standard.save()
        self.sequence_standard = Entity(
            name='Seq1',
            project_id=self.project.id,
            entity_type_id=self.sequence_type.id
        )
        self.sequence_standard.save()
        self.shot_standard = Entity(
            name='P001',
            project_id=self.project_standard.id,
            entity_type_id=self.shot_type.id,
            parent_id=self.sequence_standard.id
        )
        self.shot_standard.save()
        self.output_type_cache = file_info.get_or_create_output_type("Cache")

    def test_get_tree_from_file(self):
        simple_tree = file_tree.get_tree_from_file("simple")
        self.assertIsNotNone(simple_tree["working"])

    def test_get_tree_from_project(self):
        simple_tree = file_tree.get_tree_from_project(self.project)
        self.assertIsNotNone(simple_tree["working"])

    def test_join_path(self):
        self.assertEqual(file_tree.join_path("", "PROD"), "PROD")
        self.assertEqual(file_tree.join_path("ROOT", "PROD"), "ROOT/PROD")
        self.assertEqual(
            file_tree.join_path("ROOT", "PROD", "\\"), "ROOT\\PROD")

    def test_get_root_path(self):
        tree = file_tree.get_tree_from_file("simple")
        path = file_tree.get_root_path(tree, "working", "/")
        self.assertEqual(path, "/simple/productions/")

    def test_add_version_suffix_to_file_name(self):
        file_name = "COSMOS_LANDROMAT_S01_P01"
        file_name = file_tree.add_version_suffix_to_file_name(file_name, 3)
        self.assertEqual(file_name, "COSMOS_LANDROMAT_S01_P01_v003")

    def test_get_project(self):
        project = file_tree.get_project(self.entity)
        self.assertEqual(project, self.project)

    def test_get_file_name_template(self):
        tree = file_tree.get_tree_from_file("standard")
        template = file_tree.get_file_name_template(
            tree,
            "working",
            self.shot
        )
        self.assertEqual(template, tree["working"]["file_name"]["shot"])
        template = file_tree.get_file_name_template(
            tree,
            "working",
            self.entity
        )
        self.assertEqual(template, tree["working"]["file_name"]["asset"])

    def test_get_folder_path_template(self):
        tree = file_tree.get_tree_from_file("simple")
        template = file_tree.get_folder_path_template(
            tree,
            "working",
            self.shot
        )
        self.assertEqual(template, tree["working"]["folder_path"]["shot"])
        template = file_tree.get_folder_path_template(
            tree,
            "working",
            self.entity
        )
        self.assertEqual(template, tree["working"]["folder_path"]["asset"])

    def test_get_folder_from_datatype_project(self):
        path = file_tree.get_folder_from_datatype(
            "Project",
            self.shot,
            self.shot_task
        )
        self.assertEquals(path, self.project.name)

    def test_get_folder_from_datatype_shot(self):
        path = file_tree.get_folder_from_datatype(
            "Shot",
            self.shot,
            self.shot_task
        )
        self.assertEquals(path, self.shot.name)

    def test_get_folder_from_datatype_sequence(self):
        path = file_tree.get_folder_from_datatype(
            "Sequence",
            self.shot,
            self.shot_task
        )
        self.assertEquals(path, self.sequence.name)

    def test_get_folder_from_datatype_episode(self):
        path = file_tree.get_folder_from_datatype(
            "Episode",
            self.shot,
            self.task
        )
        self.assertEquals(path, "E01")

    def test_get_folder_from_datatype_asset(self):
        path = file_tree.get_folder_from_datatype(
            "Asset",
            self.entity,
            self.task
        )
        self.assertEquals(path, self.entity.name)

    def test_get_folder_from_datatype_asset_type(self):
        path = file_tree.get_folder_from_datatype(
            "AssetType",
            self.entity,
            self.task
        )
        self.assertEquals(path, self.entity_type.name)

    def test_get_folder_from_datatype_department(self):
        path = file_tree.get_folder_from_datatype(
            "Department",
            self.entity,
            self.task
        )
        self.assertEquals(path, self.department.name)

    def test_get_folder_from_datatype_task(self):
        path = file_tree.get_folder_from_datatype(
            "Task",
            self.entity,
            self.task
        )
        self.assertEquals(path, self.task.name)

    def test_get_folder_from_datatype_task_type(self):
        path = file_tree.get_folder_from_datatype(
            "TaskType",
            self.entity,
            self.task
        )
        self.assertEquals(path, self.task_type.name)

    def test_get_folder_from_datatype_software(self):
        path = file_tree.get_folder_from_datatype(
            "Software",
            self.entity,
            self.task,
            software="maya"
        )
        self.assertEquals(path, "maya")

    def test_get_folder_from_datatype_output_type(self):
        path = file_tree.get_folder_from_datatype(
            "OutputType",
            self.entity,
            self.task,
            output_type=self.output_type_cache
        )
        self.assertEquals(path, "cache")

    def test_get_folder_raise_exception(self):
        self.assertRaises(
            MalformedFileTreeException,
            file_tree.get_folder_from_datatype,
            "Unknown",
            self.entity,
            self.task
        )

    def test_get_folder_path_shot(self):
        path = file_tree.get_folder_path(
            self.shot_task,
            mode="working"
        )
        self.assertEquals(
            path,
            "/simple/productions/cosmos_landromat/shots/s01/p01/animation/"
            "3dsmax"
        )

    def test_get_folder_path_with_separator(self):
        path = file_tree.get_folder_path(
            self.shot_task,
            mode="working",
            sep="\\"
        )
        self.assertEquals(
            path,
            "/simple\\productions\\cosmos_landromat\\shots\\s01\\p01\\"
            "animation\\3dsmax"
        )

    def test_get_folder_path_with_outputtype(self):
        path = file_tree.get_folder_path(
            self.shot_task,
            mode="output",
            output_type=self.output_type_cache,
            sep="/"
        )
        self.assertEquals(
            path,
            "/simple/productions/export/cosmos_landromat/shots/s01/p01/"
            "animation/cache"
        )

    def test_get_folder_path_asset(self):
        path = file_tree.get_folder_path(
            self.task,
            mode="working",
            software="maya"
        )
        self.assertEquals(
            path,
            "/simple/productions/cosmos_landromat/assets/props/tree/shaders/"
            "maya"
        )

    def test_get_file_name_asset(self):
        file_name = file_tree.get_file_name(
            self.task,
            mode="working",
            version=3
        )
        self.assertEquals(file_name, "cosmos_landromat_props_tree_shaders_v003")

    def test_get_file_name_output_asset(self):
        file_name = file_tree.get_file_name(
            self.task,
            mode="output",
            version=3
        )
        self.assertEquals(
            file_name,
            "cosmos_landromat_props_tree_shaders_geometry_v003"
        )

    def test_get_file_name_shot(self):
        file_name = file_tree.get_file_name(
            self.shot_task,
            mode="working",
            version=3
        )
        self.assertEquals(file_name, "cosmos_landromat_s01_p01_animation_v003")

    def test_get_file_path_asset(self):
        file_name = file_tree.get_file_path(
            self.task,
            software="maya",
            version=3
        )
        self.assertEquals(
            file_name,
            "/simple/productions/cosmos_landromat/assets/props/tree/shaders/"
            "maya/"
            "cosmos_landromat_props_tree_shaders_v003"
        )

    def test_change_folder_path_separators(self):
        result = file_tree.change_folder_path_separators(
            "/simple/big_buck_bunny/props", "\\")
        self.assertEqual(result, "\\simple\\big_buck_bunny\\props")

    def test_update_variable(self):
        name = file_tree.update_variable(
            "<AssetType>_<Asset>",
            self.entity,
            self.task
        )
        self.assertEquals(name, "props_tree")

    def test_apply_style(self):
        file_name = "Shaders"
        result = file_tree.apply_style(file_name, "uppercase")
        self.assertEqual(result, "SHADERS")
        result = file_tree.apply_style(file_name, "lowercase")
        self.assertEqual(result, "shaders")
