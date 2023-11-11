from rest_framework import viewsets,mixins,status
from rest_framework.response import Response

from core.utils.exception import CustomValidation
from ..serializers import monthly_salary_structure as monthly_salary_structure_serializer
from core.utils import CustomPagination,response_data,helper_function
from ..models import monthly_salary_structure as monthly_salary_structure_models


class CreateMonthlySalaryView(mixins.ListModelMixin,mixins.CreateModelMixin,mixins.DestroyModelMixin,viewsets.GenericViewSet):
    serializer_class= monthly_salary_structure_serializer.MonthSalaryStructureCreationSerializer


    def create(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data,context={'request':request})
        serialized.is_valid(raise_exception=True)
        instance = serialized.save()
        clean_data = monthly_salary_structure_serializer.MonthSalaryStructureCleanerSerializer(instance,many=False)
        data = response_data(201, "Created Successfull",clean_data.data)
        return Response(data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        structure_type= request.query_params.get('structure_type','monthly')
        datalist = monthly_salary_structure_models.MonthlySalaryStructure.objects.filter(structure_type=structure_type)

        serialized = monthly_salary_structure_serializer.MonthSalaryStructureCleanerSerializer(datalist,many=True)
        data = response_data(200, "Created Successfull",serialized.data)
        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance_id = request.data.get('id',None)
        if not monthly_salary_structure_models.MonthlySalaryStructure.objects.filter(id=instance_id).exists():
            raise CustomValidation(
            detail='Does Not exists',field='error',status_code=status.HTTP_400_BAD_REQUEST
            )
        instance = monthly_salary_structure_models.MonthlySalaryStructure.objects.get(id=instance_id)
        instance.delete()

        data = response_data(200, "Deleted Successfull",[])
        return Response(data, status=status.HTTP_204_NO_CONTENT)