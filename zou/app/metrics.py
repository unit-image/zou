"""
Components to initialize and configure served metrics at application
level.
"""
import copy
import os

from flask import request
from prometheus_flask_exporter import _to_status_code
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics


def init_metrics():
    """
    Initialize the metrics object.
    """
    prometheus_multiproc_dir = os.getenv('PROMETHEUS_MULTIPROC_DIR')
    if prometheus_multiproc_dir and not os.path.isdir(prometheus_multiproc_dir):
        os.makedirs(prometheus_multiproc_dir)

    return GunicornPrometheusMetrics.for_app_factory()


def configure_metrics(app, metrics):
    """
    Configure default metrics at application level.
    """
    with app.app_context():
        # Default metrics (duration).
        # Use endpoint as group_by but add blueprint as a default label
        # to allow future filtering.
        # `prometheus_flask_exporter` does not allow to set multiple labels at
        # init, so we need to set an hidden variable `_default_labels` and restore
        # it after.
        previous_default_labels = copy.copy(metrics._default_labels)
        metrics._default_labels.update({
            'blueprint': lambda: request.blueprint,
        })
        metrics.export_defaults(
            group_by='endpoint',
            latency_as_histogram=False,
            prefix='flask_endpoint',
            app=app,
        )
        metrics._default_labels = previous_default_labels

        # counter metrics
        if os.getenv('EXPORT_PATH_METRICS', False):
            metrics.register_default(
                metrics.counter(
                    'by_path_counter', 'Request count by request paths',
                    labels={
                        'path': lambda: request.path,
                        'endpoint': lambda: request.endpoint,
                        'blueprint': lambda: request.blueprint,
                        'method': lambda: request.method,
                        'status': lambda r: _to_status_code(r.status_code),
                    }
                )
            )

        metrics.register_default(
            metrics.counter(
                'by_endpoint_counter', 'Request count by request endpoints',
                labels={
                    'endpoint': lambda: request.endpoint,
                    'blueprint': lambda: request.blueprint,
                    'method': lambda: request.method,
                    'status': lambda r: _to_status_code(r.status_code),
                }
            )
        )

        metrics.register_default(
            metrics.counter(
                'by_blueprint_counter', 'Request count by request blueprints',
                labels={
                    'blueprint': lambda: request.blueprint,
                    'method': lambda: request.method,
                    'status': lambda r: _to_status_code(r.status_code),
                }
            )
        )
