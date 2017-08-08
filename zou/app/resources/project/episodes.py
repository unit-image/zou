from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.utils import query
from zou.app.project import shot_info
from zou.app.models.entity import Entity
from zou.app.project.exception import EpisodeNotFoundException


class EpisodeResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve given episode.
        """
        try:
            episode = shot_info.get_episode(instance_id)
        except EpisodeNotFoundException:
            abort(404)
        return episode.serialize(obj_type="Episode")


class EpisodesResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self):
        """
        Retrieve all episode entries. Filters can be specified in the query
        string.
        """
        criterions = query.get_query_criterions_from_request(request)
        episodes = shot_info.get_episodes(criterions)
        return Entity.serialize_list(episodes, obj_type="Episode")


class EpisodeSequencesResource(Resource):

    def __init__(self):
        Resource.__init__(self)

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve all sequence entries for a given episode.
        Filters can be specified in the query string.
        """
        criterions = query.get_query_criterions_from_request(request)
        criterions["parent_id"] = instance_id
        sequences = shot_info.get_sequences(criterions)
        return Entity.serialize_list(sequences, obj_type="Sequence")
