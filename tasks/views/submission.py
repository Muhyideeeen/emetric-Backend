from django.core.exceptions import ValidationError
from core.utils import (
    CustomPagination,
    NestedMultipartParser,
    permissions,
    response_data,
)
from rest_framework import generics, status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.utils.exception import CustomValidation
from core.utils.permissions import IsSuperAdminUserOnly, IsAdminUserOnly
from tasks.models.submission import TaskSubmission
from tasks.serializers import TaskSubmissionSerializer


class TaskSubmissionCreateView(generics.CreateAPIView):
    """Task submission create view"""

    serializer_class = TaskSubmissionSerializer
    permissions_classes = [IsAuthenticated]
    queryset = TaskSubmission.objects.all()
    parser_classes = (NestedMultipartParser, JSONParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "Task Submission has been added successfully", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)


class TaskSubmissionListView(generics.ListAPIView):
    serializer_class = TaskSubmissionSerializer
    pagination_class = CustomPagination
    permissions_class = [
        IsAuthenticated,
    ]
    queryset = TaskSubmission.objects.all()
    lookup_field = "task_id"

    def get_queryset(self):

        if self.lookup_field is None:
            return None
        task_id = self.kwargs[self.lookup_field]

        try:
            queryset = TaskSubmission.objects.filter(task__task_id=task_id)
        except ValidationError:
            raise CustomValidation(
                detail=f"{task_id} is not valid uuid", field="task_id", status_code=400
            )
        return queryset
