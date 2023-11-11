from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import monthly_salary_structure,generated_views


route = DefaultRouter()
route.register('create',monthly_salary_structure.CreateMonthlySalaryView,basename='create-monthly-salary')
route.register('monthly_generate',generated_views.generatedMonthlyStructureViewSet,basename='monthly_generate')
urlpatterns = [

] + route.urls