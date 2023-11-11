"""
celery config module
"""
import os

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_metric_api.settings")


from tenant_schemas_celery.app import CeleryApp as TenantAwareCeleryApp
from celery.schedules import crontab


app = TenantAwareCeleryApp()

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Note: celery worker must be run with "default" queue defined
# app.conf.task_default_queue = "default"
# from django_tenants_celery_beat.utils import generate_beat_schedule

# app.conf.beat_schedule = generate_beat_schedule(
#     {
#         "celery.backend_cleanup": {
#             "task": "celery.backend_cleanup",
#             "schedule": crontab("0", "4", "*"),
#             "options": {"expire_seconds": 12 * 3600},
#             "tenancy_options": {
#                 "public": False,
#                 "all_tenants": True,
#                 "use_tenant_timezone": True,
#             }
#         },
#     }
# )
