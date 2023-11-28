from flask_restful import reqparse
from flask import request

from zou.app.utils import fields
from zou.app.services.exception import WrongParameterException


class ArgsMixin(object):
    """
    Helpers to retrieve parameters from GET or POST queries.
    """

    def get_args(self, descriptors):
        parser = reqparse.RequestParser()
        for descriptor in descriptors:
            action = None

            if len(descriptor) == 4:
                (name, default, required, action) = descriptor
            else:
                (name, default, required) = descriptor

            parser.add_argument(
                name, required=required, default=default, action=action
            )

        return parser.parse_args()

    def clear_empty_fields(self, data):
        """
        Remove fiels set to None from data dict.
        """
        for key in list(data.keys()):
            if data[key] is None:
                del data[key]
        return data

    def get_page(self):
        """
        Returns page requested by the user.
        """
        options = request.args
        return int(options.get("page", "-1"))

    def get_force(self):
        """
        Returns force parameter.
        """
        options = request.args
        return options.get("force", "false") == "true"

    def get_relations(self):
        """
        Returns force parameter.
        """
        options = request.args
        return options.get("relations", "false") == "true"

    def get_episode_id(self):
        """
        Returns episode ID parameter.
        """
        options = request.args
        return options.get("episode_id", None)

    def parse_date_parameter(self, param):
        date = None
        if param is None:
            return date
        formats = [
            r"%Y-%m-%dT%H:%M:%S.%f",
            r"%Y-%m-%dT%H:%M:%S",
            r"%Y-%m-%d",
        ]
        for format in formats:
            try:
                date = fields.get_date_object(param, format)
                break
            except ValueError:
                continue
        else:
            raise WrongParameterException(
                "Wrong date format for before argument."
                "Expected format: 2020-01-05T13:23:10.123456, 2020-01-05T13:23:10 or 2020-01-05"
            )

        return date
