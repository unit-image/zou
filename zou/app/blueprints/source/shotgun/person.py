from flask_restful import current_app

from zou.app import db
from zou.app.models.department import Department
from zou.app.models.person import Person, department_link as DepartmentLink
from zou.app.utils import auth
from zou.app.blueprints.source.shotgun.exception import (
    ShotgunEntryImportFailed
)
from zou.app.blueprints.source.shotgun.base import (
    BaseImportShotgunResource,
    ImportRemoveShotgunBaseResource
)
from zou.app.services import tasks_service


class ImportShotgunPersonsResource(BaseImportShotgunResource):

    def __init__(self):
        BaseImportShotgunResource.__init__(self)

    def extract_data(self, sg_person):
        is_active = sg_person.get("sg_status_list", "act") == "act"
        role = "user"

        rule_set = sg_person.get("permission_rule_set", {})
        permission_group = rule_set.get("name", "")
        if permission_group == "Manager":
            role = "manager"
        elif permission_group == "Admin":
            role = "admin"

        if sg_person['department']:
            department = tasks_service.get_or_create_department(
                sg_person['department']['name']
            )
        else:
            department = None

        return {
            "first_name": sg_person["firstname"],
            "last_name": sg_person["lastname"],
            "email": sg_person["email"],
            "shotgun_id": sg_person["id"],
            "desktop_login": sg_person["login"],
            "active": is_active,
            "role": role,
            "department": department
        }

    def import_entry(self, data):
        # remove departments. It needs to be created using the DepartmentLink
        # table.
        imported_department = data.pop('department')

        if data["email"] != "changeme@email.com":
            person = Person.get_by(shotgun_id=data["shotgun_id"])
            if person is None:
                person = Person.get_by(email=data["email"])

            if person is None:
                data["password"] = auth.encrypt_password("default")
                person = Person(**data)
                person.save()
                current_app.logger.info("Person created: %s" % person)
            else:
                if person.password is None or len(person.password) == 0:
                    data["password"] = auth.encrypt_password("default")

            # create or update a department/person link if needed
            if imported_department:
                department_person_link = \
                    db.session.query(DepartmentLink).filter_by(
                        person_id=person.id).first()
                department = Department.get_by(
                    id=imported_department['id'])

                if department_person_link is None:
                    person.skills.append(department)
                    current_app.logger.info(
                        "Department Person Link created: %s-%s" % (
                            department.name,
                            person.full_name()
                        ))
                elif person.skills != [department, ]:
                    person.skills = [department, ]
                    current_app.logger.info(
                        "Department Person Link updated: %s-%s" % (
                            department.name,
                            person.full_name()
                        ))

                person.save()

            return person

        else:
            raise ShotgunEntryImportFailed("This entry is not a real person.")


class ImportRemoveShotgunPersonResource(ImportRemoveShotgunBaseResource):

    def __init__(self):
        ImportRemoveShotgunBaseResource.__init__(self, Person)
