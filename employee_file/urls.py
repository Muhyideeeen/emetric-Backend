"""
employee file setup url config
"""
from django.urls import path
from rest_framework.routers import SimpleRouter

from employee_file.views import EmployeeFileViewSet, EmployeeFileNameViewSet

app_name = "employee-file"

router = SimpleRouter()
router.register(r"employee-file", EmployeeFileViewSet, basename="employee-file")
router.register(
    r"employee-file-name", EmployeeFileNameViewSet, basename="employee-file-name"
)


urlpatterns = []

urlpatterns += router.urls
