from payroll.models import generated_employee_montly_structure  as gen_models
from rest_framework import viewsets,status,mixins
from rest_framework.response import Response
from ..serializers import generated_payroll_serializer
from core.utils import CustomPagination,response_data,helper_function
from rest_framework.decorators import action
import payroll.filter as customfilter

class generatedMonthlyStructureViewSet( mixins.ListModelMixin,mixins.CreateModelMixin,viewsets.GenericViewSet):
    serializer_class = generated_payroll_serializer.generatedMonthlyStructureSerializer
    queryset=gen_models.EmployeeSavedMonthlySalaryStructure.objects.all()
    filterset_class =customfilter.generatedMonthlyFilter
    def create(self, request, *args, **kwargs):
        'when a request is sent here it trigggers generating the EmployeeSavedMonthlySalaryStructure '
        serialized = self.serializer_class(data=request.data,context={'request':request})
        serialized.is_valid(raise_exception=True)
        d=serialized.save()
        data = response_data(201, "Generated Successfull",[d])
        return Response(data, status=status.HTTP_201_CREATED)

    def list(self,request,*args,**kwargs):
        'this will return  the generatedMonthlyStructureSerializer by date selected'
        queryset =self.filter_queryset(self.get_queryset().order_by('grade_level'))
        clean_data = generated_payroll_serializer.cleanGeneratedEmployeeSavedMonthlySalaryStructure(queryset,many=True)
        data = response_data(200, "Generated Successfull",clean_data.data)
        return Response(data,status=status.HTTP_200_OK)
 


    @action(['get'],detail=False)
    def get_available_generated_dates(self,request,format=False):
        structure_type= request.query_params.get('structure_type','monthly')
        data = gen_models.EmployeeSavedMonthlySalaryStructure.objects.filter(structure_type=structure_type).values('created_on','generated_for','updated_at','structure_type')
        res_data = response_data(201, "Success",data)

        return  Response(data, status=status.HTTP_200_OK)