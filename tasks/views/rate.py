from rest_framework import generics, status
from rest_framework.response import Response

from core.utils import response_data
from core.utils.permissions import IsTaskAssignorOrAdminOrReadOnly
from tasks.models import Task
from tasks.serializers import TaskRatingSerializer, TaskReworkSerializer


class TaskRateView(generics.UpdateAPIView):
    serializer_class = TaskRatingSerializer
    permission_classes = [
        IsTaskAssignorOrAdminOrReadOnly,
    ]
    queryset = Task.objects.all()
    lookup_field = "task_id"

    def patch(self, request, *args, **kwargs):
        data = response_data(405, "This method is not allowed for this resource", [])
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        data = response_data(200, "Task rated successfully", serializer.data)
        return Response(data, status=status.HTTP_200_OK)


class TaskReworkView(generics.UpdateAPIView):
    serializer_class = TaskReworkSerializer
    permission_classes = [
        IsTaskAssignorOrAdminOrReadOnly,
    ]
    queryset = Task.objects.all()
    lookup_field = "task_id"

    def patch(self, request, *args, **kwargs):
        data = response_data(405, "This method is not allowed for this resource", [])
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        data = response_data(200, "Task rework has been submitted successfully", serializer.data)
        return Response(data, status=status.HTTP_200_OK)