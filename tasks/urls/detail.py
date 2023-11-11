"""
task setup url config
"""
from django.urls import path

from tasks.views import (
    TaskListCreateView,
    TaskDetailView,
    TaskSubmissionListView,
    TaskRateView,
    TaskReworkView,
    TaskImportView,
    user_task_report,
    team_task_report,
    initiative_task_report,
    objective_task_report,
    ObjectiveReport,
    TeamInitiativeReport,
    MultipleTaskDeleteView,
)


app_name = "task"

urlpatterns = [
    path("", TaskListCreateView.as_view(), name="task-create-list"),
    path(
        "report/user/<str:user_id>/", user_task_report, name="task-report-user"
    ),
    path(
        "report/team/<str:team_id>/", team_task_report, name="task-report-team"
    ),
    path(
        "report/team-initiative/<str:team_id>/",
        TeamInitiativeReport.as_view(),
        name="initiative-report-team",
    ),
    path(
        "report/initiative/<str:initiative_id>/",
        initiative_task_report,
        name="task-report-initiative",
    ),
    path(
        "report/objective/<str:objective_id>/",
        objective_task_report,
        name="task-report-objective",
    ),
    path(
        "report/objective/",
        ObjectiveReport.as_view(),
        name="objective-report",
    ),
    path("bulk-add/", TaskImportView.as_view(), name="task-bulk-add"),
    path(
        "bulk-delete/",
        MultipleTaskDeleteView.as_view(),
        name="task-bulk-delete",
    ),
    path("<str:task_id>/", TaskDetailView.as_view(), name="task-detail"),
    path(
        "<str:task_id>/task-submission/",
        TaskSubmissionListView.as_view(),
        name="fetch-submission-by-task",
    ),
    path("<str:task_id>/rate/", TaskRateView.as_view(), name="task-rate"),
    path(
        "<str:task_id>/rework/", TaskReworkView.as_view(), name="task-rework"
    ),
]
