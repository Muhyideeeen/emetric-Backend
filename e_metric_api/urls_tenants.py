"""e_metric_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from account.views.user import GetUsersByRoleView, GetCurrentOrganisationView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("account.urls.tenant-auth")),
    path("employee/", include("employee.urls")),
    path("", include("employee_file.urls")),
    path("calendar/", include("emetric_calendar.urls")),
    path("designation/", include("designation.urls")),
    path("career-path/", include("career_path.urls")),
    path("roles/", include("account.urls.role")),
    path("perspective/", include("strategy_deck.urls.perspective")),
    path("objective/", include("strategy_deck.urls.objective")),
    path("initiative/", include("strategy_deck.urls.initiative")),
    path("task/", include("tasks.urls.detail")),
    path("task-submission/", include("tasks.urls.submission")),
    path(
        "role/<str:role_name>/users/",
        GetUsersByRoleView.as_view(),
        name="fetch-users-by-roles",
    ),
    path(
        "organisation/current/",
        GetCurrentOrganisationView.as_view(),
        name="fetch-current-organisation",
    ),
    path('leave-management/',include('leaveManagement.urls')),
    path('payroll/',include('payroll.urls'))
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += [
        path("silk/", include("silk.urls", namespace="silk-tenants"))
    ]
