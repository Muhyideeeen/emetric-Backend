from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from core.utils import response_data
from organization.serializers.bulk_add import OrganisationImportSerializer
from core.utils.permissions import IsAdminOrHRAdminOrReadOnly
from organization.models import CorporateLevel


class OrganisationImportView(generics.CreateAPIView):
    serializer_class = OrganisationImportSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = CorporateLevel.objects.all()
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(
            201,
            "Organisation Levels have been added from excel sheet successfully",
            [],
        )
        return Response(data, status=status.HTTP_201_CREATED)
