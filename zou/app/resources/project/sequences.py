from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.utils import query
from zou.app.project import shot_info
from zou.app.models.entity import Entity
from zou.app.project.exception import SequenceNotFoundException


class SequenceResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve given sequence.
        """
        try:
            sequence = shot_info.get_sequence(instance_id)
        except SequenceNotFoundException:
            abort(404)
        return sequence.serialize(obj_type="Sequence")


class SequencesResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self):
        """
        Retrieve all sequence entries. Filters can be specified in the query
        string.
        """
        criterions = query.get_query_criterions_from_request(request)
        sequences = shot_info.get_sequences(criterions)
        return Entity.serialize_list(sequences, obj_type="Sequence")


class SequenceShotsResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve all shot entries for a given sequence.
        Filters can be specified in the query string.
        """
        criterions = query.get_query_criterions_from_request(request)
        criterions["parent_id"] = instance_id
        return shot_info.get_shots(criterions)
