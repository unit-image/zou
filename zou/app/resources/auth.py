from flask_restful import Resource, reqparse, current_app
from zou.app.project.exception import PersonNotFoundException

from zou.app.utils import auth
from zou.app.project import person_info

from zou.app import app

from flask_jwt_extended import (
    jwt_required,
    jwt_refresh_token_required,
    create_access_token,
    create_refresh_token,
    revoke_token,
    get_jwt_identity,
    get_raw_jwt
)


class AuthenticatedResource(Resource):

    @jwt_required
    def get(self):
        person = person_info.get_by_email(get_jwt_identity())
        return {
            "authenticated": True,
            "user": person.serialize()
        }


class LogoutResource(Resource):

    @jwt_required
    def get(self):
        try:
            current_token = get_raw_jwt()
            jti = current_token['jti']
            revoke_token(jti)
        except KeyError:
            return {
                "Access token not found."
            }, 500
        return {
            "logout": True
        }


class LoginResource(Resource):

    def post(self):
        (email, password) = self.get_arguments()
        try:
            strategy = app.config["AUTH_STRATEGY"]
            if strategy == "auth_local_classic":
                user = auth.local_auth_strategy(email, password)
            elif strategy == "auth_local_no_password":
                user = auth.no_password_auth_strategy(email)
            elif strategy == "auth_remote_active_directory":
                user = auth.active_directory_auth_strategy(email, password)
            else:
                raise auth.NoAuthStrategyConfigured
            return {
                "user": user,
                "access_token": create_access_token(identity=email),
                "refresh_token": create_refresh_token(identity=email)
            }
        except PersonNotFoundException:
            current_app.logger.info("User is not registered.")
            return {"login": False}, 400
        except auth.WrongPasswordException:
            current_app.logger.info("User gave a wrong password.")
            return {"login": False}, 400
        except auth.NoAuthStrategyConfigured:
            current_app.logger.info(
                "Authentication strategy is not properly configured."
            )
            return {"login": False}, 400

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "email",
            required=True,
            help="User email is missing."
        )
        parser.add_argument("password", default="")
        args = parser.parse_args()

        return (
            args["email"],
            args["password"],
        )


class RefreshTokenResource(Resource):

    @jwt_refresh_token_required
    def get(self):
        email = get_jwt_identity()
        return {
            "access_token": create_access_token(identity=email)
        }


class RegistrationResource(Resource):

    def post(self):
        (
            email,
            password,
            password_2,
            first_name,
            last_name
        ) = self.get_arguments()

        try:
            email = auth.validate_email(email)
            auth.validate_password(password, password_2)
            password = auth.encrypt_password(password)
            person_info.create_person(email, password, first_name, last_name)
            return {"registration_success": True}, 201
        except auth.PasswordsNoMatchException:
            return {
                "error": True,
                "message": "Confirmation password doesn't match."
            }, 400
        except auth.PasswordTooShortException:
            return {
                "error": True,
                "message": "Password is too short."
            }, 400
        except auth.EmailNotValidException as exception:
            return {
                "error": True,
                "message": str(exception)
            }, 400

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "email",
            required=True,
            help="User email is missing."
        )
        parser.add_argument(
            "first_name",
            required=True,
            help="First name is missing."
        )
        parser.add_argument(
            "last_name",
            required=True,
            help="Last name is missing."
        )
        parser.add_argument(
            "password",
            required=True,
            help="Password is missing."
        )
        parser.add_argument(
            "password_2",
            required=True,
            help="Confirmation password is missing."
        )
        args = parser.parse_args()

        return (
            args["email"],
            args["password"],
            args["password_2"],
            args["first_name"],
            args["last_name"]
        )


class ChangePasswordResource(Resource):

    @jwt_required
    def post(self):
        (
            old_password,
            password,
            password_2,
        ) = self.get_arguments()

        try:
            auth.check_credentials(get_jwt_identity(), old_password)
            auth.validate_password(password, password_2)
            password = auth.encrypt_password(password)
            person_info.update_password(get_jwt_identity(), password)
            return {"change_password_success": True}

        except auth.PasswordsNoMatchException:
            return {
                "error": True,
                "message": "Confirmation password doesn't match."
            }, 400
        except auth.PasswordTooShortException:
            return {
                "error": True,
                "message": "Password is too short."
            }, 400
        except auth.WrongPasswordException:
            return {
                "error": True,
                "message": "Old password is wrong."
            }, 400

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "old_password",
            required=True,
            help="Old password is missing."
        )
        parser.add_argument(
            "password",
            required=True,
            help="New password is missing."
        )
        parser.add_argument(
            "password_2",
            required=True,
            help="New password confirmation is missing."
        )
        args = parser.parse_args()

        return (
            args["old_password"],
            args["password"],
            args["password_2"]
        )


class PersonListResource(Resource):
    """
    Resource used to list people available in the database without being logged.
    It is used currently by some studios that rely on authentication without
    password.
    """

    def get(self):
        person_names = []
        for person in person_info.all():
            person_names.append({
                "id": str(person.id),
                "email": person.email,
                "first_name": person.first_name,
                "last_name": person.last_name
            })
        return person_names
