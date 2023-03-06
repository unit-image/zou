"""
Configure file for gunicorn main process.

It currently:
- handles part of the exporting of prometheus metrics by starting a server and
  gather metrics of child processes.
"""
import os

from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

prometheus_multiproc_dir = os.environ['PROMETHEUS_MULTIPROC_DIR']
if not os.path.isdir(prometheus_multiproc_dir):
    os.makedirs(prometheus_multiproc_dir)


def when_ready(server):
    GunicornPrometheusMetrics.start_http_server_when_ready(9180)


def child_exit(server, worker):
    GunicornPrometheusMetrics.mark_process_dead_on_child_exit(worker.pid)
