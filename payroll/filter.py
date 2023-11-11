import django_filters
from .models import generated_employee_montly_structure as gen_models





class generatedMonthlyFilter(django_filters.FilterSet):
    generated_for= django_filters.DateFilter(field_name='generated_for')
    structure_type= django_filters.CharFilter(field_name='structure_type')


    class Meta:
        model = gen_models.EmployeeSavedMonthlySalaryStructure
        fields = ['generated_for','structure_type']