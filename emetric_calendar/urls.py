"""
employee_calender setup url config
"""
from django.urls import path
from rest_framework.routers import SimpleRouter

from emetric_calendar.views import (
    HolidayViewsets,
    UserScheduledEventCalendarView,
    TeamScheduledEventCalendarView,
    UserCalendarDashboardView,
    TeamCalendarDashboardView,
)


app_name = "emetric_calendar"
router = SimpleRouter()
router.register(r"holiday", HolidayViewsets, basename="holiday")

urlpatterns = [
    path(
        "user/<str:user_id>/",
        UserScheduledEventCalendarView.as_view(),
        name="user-calendar",
    ),
    path(
        "team/<str:team_id>/",
        TeamScheduledEventCalendarView.as_view(),
        name="team-calendar",
    ),
    path(
        "user/<str:user_id>/dashboard/",
        UserCalendarDashboardView.as_view(),
        name="user-calendar-dashboard",
    ),
    path(
        "team/<str:team_id>/dashboard/",
        TeamCalendarDashboardView.as_view(),
        name="team-calendar-dashboard",
    ),
]
urlpatterns += router.urls
