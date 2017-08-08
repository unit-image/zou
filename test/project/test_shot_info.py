from test.base import ApiDBTestCase

from zou.app.project import shot_info
from zou.app.project.exception import SequenceNotFoundException


class ShotUtilsTestCase(ApiDBTestCase):

    def setUp(self):
        super(ShotUtilsTestCase, self).setUp()

        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_entity_type()
        self.generate_fixture_episode()
        self.generate_fixture_sequence()
        self.generate_fixture_shot()
        self.generate_fixture_entity()

    def test_get_sequence_from_shot(self):
        sequence = shot_info.get_sequence_from_shot(self.shot)
        self.assertEquals(sequence.name, 'S01')

    def test_get_episode_from_shot(self):
        episode = shot_info.get_episode_from_sequence(self.sequence)
        self.assertEquals(episode.name, 'E01')

    def test_get_sequence_from_shot_no_sequence(self):
        self.assertRaises(
            SequenceNotFoundException,
            shot_info.get_sequence_from_shot,
            self.shot_noseq
        )

    def test_get_sequence_type(self):
        sequence_type = shot_info.get_sequence_type()
        self.assertEqual(sequence_type.name, "Sequence")

    def test_get_shot_type(self):
        shot_type = shot_info.get_shot_type()
        self.assertEqual(shot_type.name, "Shot")

    def test_get_episode_type(self):
        episode_type = shot_info.get_episode_type()
        self.assertEqual(episode_type.name, "Episode")

    def test_get_sequences(self):
        sequences = shot_info.get_sequences()
        self.assertDictEqual(
            sequences[0].serialize(),
            self.sequence.serialize()
        )

    def test_get_shots(self):
        shots = shot_info.get_shots()
        self.shot_dict = self.shot.serialize(obj_type="Shot")
        self.shot_dict["project_name"] = self.project.name
        self.shot_dict["sequence_name"] = self.sequence.name

        self.assertDictEqual(shots[0], self.shot_dict)

    def test_get_shots_and_tasks(self):
        self.generate_fixture_person()
        self.generate_fixture_assigner()
        self.generate_fixture_department()
        self.generate_fixture_task_status()
        self.generate_fixture_task_type()
        self.generate_fixture_shot_task()
        self.generate_fixture_shot_task(name="Secondary")
        shots = shot_info.get_shots_and_tasks()
        self.assertEqual(len(shots), 1)
        self.assertEqual(len(shots[0]["tasks"]), 2)
        self.assertEqual(
            shots[0]["tasks"][0]["task_status_name"], "Open"
        )
        self.assertEqual(
            shots[0]["tasks"][0]["task_type_name"], "Animation"
        )

    def test_is_shot(self):
        self.assertTrue(shot_info.is_shot(self.shot))
        self.assertFalse(shot_info.is_shot(self.entity))

    def test_get_shot(self):
        self.assertEquals(self.shot.id, shot_info.get_shot(self.shot.id).id)

    def test_get_sequence(self):
        self.assertEquals(
            self.sequence.id,
            shot_info.get_sequence(self.sequence.id).id
        )

    def test_get_episode(self):
        self.assertEquals(
            self.episode.id,
            shot_info.get_episode(self.episode.id).id
        )
