
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


route = DefaultRouter()
route.register('hr-leave-management',views.AdminLeaveManagementViewSet)
route.register('leave-application',views.EmployeeLeaveApplicationViewset)
route.register('team-lead-review-leave-application',views.TeamLeadReviewLeaveApplication)
urlpatterns = [

] +route.urls