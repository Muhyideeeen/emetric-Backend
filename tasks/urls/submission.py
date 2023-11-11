"""
task submission setup url config
"""
from django.urls import path

from tasks.views import TaskSubmissionCreateView

app_name = "task-submission"

urlpatterns = [
    path("", TaskSubmissionCreateView.as_view(), name="task-submission-create"),
]
