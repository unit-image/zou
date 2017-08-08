import math
import json
import sqlalchemy.orm as orm

from flask import request, abort
from flask_restful import Resource, current_app
from flask_jwt_extended import jwt_required

from sqlalchemy.exc import IntegrityError, StatementError


class BaseModelsResource(Resource):

    def __init__(self, model):
        Resource.__init__(self)
        self.model = model

    def all_entries(self, query=None):
        if query is None:
            query = self.model.query

        return self.model.serialize_list(query.all())

    def paginated_entries(self, query, page):
        total = query.count()
        limit = current_app.config['NB_RECORDS_PER_PAGE']
        offset = (page - 1) * limit

        if (total < offset) or (page < 1):
            abort(404)

        nb_pages = int(math.ceil(total / float(limit)))
        query = query.limit(limit)
        query = query.offset(offset)

        result = {
            "data": self.all_entries(query),
            "total": total,
            "nb_pages": nb_pages,
            "limit": limit,
            "offset": offset,
            "page": page
        }
        return result

    def build_filters(self, options):
        many_join_filter = []
        in_filter = []
        filters = {}

        for key, value in options.items():
            if key != "page":
                field_key = getattr(self.model, key)
                expr = field_key.property

                is_many_to_many_field = isinstance(
                    expr, orm.properties.RelationshipProperty
                )
                value_is_list = len(value) > 0 and value[0] == '['

                if is_many_to_many_field:
                    many_join_filter.append((key, value))

                elif value_is_list:
                    value_array = json.loads(value)
                    in_filter.append(field_key.in_(value_array))

                else:
                    filters[key] = value

        return (many_join_filter, in_filter, filters)

    def apply_filters(self, query):
        (
            many_join_filter,
            in_filter,
            criterions
        ) = self.build_filters(query)

        query = self.model.query.filter_by(**criterions)

        for id_filter in in_filter:
            query = query.filter(id_filter)

        for (key, value) in many_join_filter:
            query = query.filter(getattr(self.model, key).any(id=value))

        return query

    @jwt_required
    def get(self):
        """
        Retrieve all entries for given model. Filters can be specified in the
        query string.
        """
        query = self.model.query
        if not request.args:
            return self.all_entries(query)
        else:
            options = request.args
            query = self.apply_filters(options)
            page = int(options.get("page", "-1"))
            is_paginated = page > -1

            if is_paginated:
                return self.paginated_entries(query, page)
            else:
                return self.all_entries(query)

    @jwt_required
    def post(self):
        """
        Create a model with data given in the request body. JSON format is
        expected. The model performs the validation automatically when
        instantiated.
        """
        try:
            instance = self.model(**request.json)
            instance.save()
            return instance.serialize(), 201

        except TypeError as exception:
            current_app.logger.error(str(exception))
            return {"error": str(exception)}, 400

        except IntegrityError as exception:
            current_app.logger.error(str(exception))
            return {"error": str(exception)}, 400

        except StatementError as exception:
            current_app.logger.error(str(exception))
            return {"error": str(exception)}, 400


class BaseModelResource(Resource):

    def __init__(self, model):
        Resource.__init__(self)
        self.model = model

    def get_model_or_404(self, instance_id):
        instance = self.model.get(instance_id)
        if instance is None:
            abort(404)
        return instance

    @jwt_required
    def get(self, instance_id):
        """
        Retrieve a model corresponding at given ID and return it as a JSON
        object.
        """
        try:
            instance = self.get_model_or_404(instance_id)
        except StatementError:
            return {"error": "Wrong id format"}, 400
        return instance.serialize(), 200

    @jwt_required
    def put(self, instance_id):
        """
        Update a model with data given in the request body. JSON format is
        expected. Model performs the validation automatically when fields are
        modified.
        """
        try:
            instance = self.get_model_or_404(instance_id)
            instance.update(request.json)
            return instance.serialize(), 200

        except StatementError:
            return {"error": "Wrong id format"}, 400

        except TypeError as exception:
            current_app.logger.error(str(exception))
            return {"error": str(exception)}, 400

        except IntegrityError as exception:
            current_app.logger.error(str(exception))
            return {"error": str(exception)}, 400

        except StatementError as exception:
            current_app.logger.error(str(exception))
            return {"error": str(exception)}, 400

    @jwt_required
    def delete(self, instance_id):
        """
        Delete a model corresponding at given ID and return it as a JSON
        object.
        """
        instance = self.get_model_or_404(instance_id)

        try:
            instance.delete()
        except IntegrityError as exception:
            current_app.logger.error(str(exception))
            return {"error": str(exception)}, 400

        return {"deletion_success": True}, 204
