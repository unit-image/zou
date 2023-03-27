from datetime import datetime
from tests.base import ApiDBTestCase


class PersonDaysWorkedTestCase(ApiDBTestCase):

    def setUp(self):
        super(PersonDaysWorkedTestCase, self).setUp()

    def test_get_day_worked(self):
        self.generate_fixture_person()

        today = datetime.today()

        person_id = str(self.person.id)

        # Day worked creation
        self.post(
            "/data/persons/{id}/days_worked/{year}/{month}/{day}".format(
                id=person_id,
                year=today.year,
                month=today.month,
                day=today.day),
            {
                "work_duration": 0.5,
                "variable_time": -2,
                "justification": "Test day worked"
            }
        )

        # Day worked update
        self.post(
            "/data/persons/{id}/days_worked/{year}/{month}/{day}".format(
                id=person_id,
                year=today.year,
                month=today.month,
                day=today.day),
            {
                "work_duration": 1,
                "variable_time": -2,
            }
        )

        # Get day worked and check data
        day_worked = self.get(
            "/data/persons/{id}/days_worked/{year}/{month}/{day}".format(
                id=person_id,
                year=today.year,
                month=today.month,
                day=today.day
            )
        )

        self.assertEqual(day_worked["date"], today.strftime("%Y-%m-%d"))
        self.assertEqual(day_worked["work_duration"], 1)
        self.assertEqual(day_worked["variable_time"], -2)
