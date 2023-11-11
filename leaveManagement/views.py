from django.shortcuts import render
from core.utils import permissions as custom_permissions
from rest_framework.response import Response
from rest_framework import viewsets,status,permissions
from  . import models,serializers
from rest_framework.decorators import action
from core.utils import CustomPagination,response_data
from rest_framework import  filters
from rest_framework.parsers import  FormParser, JSONParser
import django_filters
from . import filter as custom_filters
from account.models.roles import Role
from core.utils.custom_parser import NestedMultipartParser


class AdminLeaveManagementViewSet(viewsets.ModelViewSet):
    'it only admin that can access this view and only hradmin that can make an big changes'
    permission_classes = [custom_permissions.IsAdminOrHRAdminOrReadOnly]
    queryset  = models.Leave.objects.all()
    serializer_class = serializers.AdminLeaveManagementSerializer
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        filter_by_grade_level_id = self.request.query_params.get('filter_by_grade_level_id',None)
        if filter_by_grade_level_id:queryset = self.queryset.filter(grade_level=filter_by_grade_level_id)
        else:queryset = self.queryset.all()
        serializer = self.serializer_class(queryset,many=True)
        # serializer.is_valid(raise_exception=True)
        data = response_data(200, "Successfull", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        for_all_level = self.request.query_params.get('for_all_level',None)
        serializer = self.serializer_class(data=request.data,context={'for_all_level':for_all_level})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if for_all_level:
            print('wowo')
            data = response_data(201, "Created Successfull", [])
        else:
            print('This DId noe','e')
            data = response_data(201, "Created Successfull", serializer.data)
        return Response(data, status=status.HTTP_201_CREATED)


    @action(detail=False,methods=['POST'],url_name='hr_review_applications')
    def hr_review_applications(self,request,pk=None):
        serializer = serializers.HRAdminReviewApplicationSerializer(data=request.data ,context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = response_data(200, "Accepted Successfull", [])
        return Response(data, status=status.HTTP_200_OK)

class EmployeeLeaveApplicationViewset(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset  = models.EmployeeLeaveApplication.objects.all()
    serializer_class = serializers.EmployeeLeaveApplicationSerializer
    pagination_class = CustomPagination
    # filter_backends
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class=custom_filters.EmployeeLeaveApplicationFilter
    parser_classes = (NestedMultipartParser,FormParser,)
    



    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if(request.user.user_role.role in [Role.TEAM_LEAD,Role.EMPLOYEE]):
            serializer = serializers.LeaveApplicationSerializerCleaner(queryset.filter(employee__id=request.user.employee.id),many=True)
        else:
            serializer = serializers.LeaveApplicationSerializerCleaner(queryset.all(),many=True)

        # serializer.is_valid(raise_exception=True)
        data = response_data(200, "Successfull", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False,methods=['POST'],url_name='get_team_leave_application')
    def get_team_leave_application(self,request,pk=None):
        queryset = self.filter_queryset(self.get_queryset())
        'we going to filter by the team id in the front end'
        serializer = serializers.LeaveApplicationSerializerCleaner(queryset.all(),many=True)

        # serializer.is_valid(raise_exception=True)
        data = response_data(200, "Successfull", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data ,context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = response_data(201, "Created Successfull", serializer.data)
        return Response(data, status=status.HTTP_201_CREATED)


class TeamLeadReviewLeaveApplication(viewsets.ModelViewSet):
    permission_classes = [custom_permissions.IsTeamLeadOnly]
    queryset  = models.EmployeeLeaveApplication.objects.all()
    serializer_class = serializers.TeamLeadReviewApplicationSerializer
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data ,context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = response_data(200, "Accepted Successfull", [])
        return Response(data, status=status.HTTP_200_OK)


    def list(self, request, *args, **kwargs):
        serializer = serializers.LeaveApplicationSerializerCleaner(self.queryset.all(),many=True)
        # serializer.is_valid(raise_exception=True)
        data = response_data(200, "Successfull", serializer.data)
        return Response(data, status=status.HTTP_200_OK)
"""
Hr Proccess for Employee leave application
Once the hr has accepted we set a celery that set employee to leave and active when the time is due
"""