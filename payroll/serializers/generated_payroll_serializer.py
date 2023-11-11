from rest_framework import serializers

from core.utils.exception import CustomValidation
from ..models import monthly_salary_structure
from ..models import generated_employee_montly_structure
from employee import models as employee_models
from django.db import transaction
from rest_framework import status
"""
steps to generate the EmployeeSavedMonthlySalaryStructure Models

    click on genreate
    get alll monlty payroll template
    for each of the template use the career path to filter the employee
    for each of the employee create  a EmployeeSavedMonthlySalaryStructure


how to get generated data 
    we first send all the available date to the front end so they can query a generated data for that time
"""


class generatedMonthlyStructureSerializer(serializers.Serializer):
    generated_for  = serializers.DateField()# for what month and year day  
    structure_type = serializers.ChoiceField(choices=['monthly','daily','hourly'])


    def validate(self, attrs):
        generated_for=attrs.get('generated_for')
        structure_type=attrs.get('structure_type')
        if  generated_employee_montly_structure.EmployeeSavedMonthlySalaryStructure.objects.filter(generated_for=generated_for,structure_type=structure_type).exists():
            raise CustomValidation(detail=f'{structure_type} already created data for this month',field='generated_for',status_code=status.HTTP_400_BAD_REQUEST)
        return super().validate(attrs)
    def create(self, validated_data):
        generated_for = validated_data.get('generated_for')
        structure_type = validated_data.get('structure_type')
        with transaction.atomic():
            all_monthly_payroll_template = monthly_salary_structure.MonthlySalaryStructure.objects.filter(structure_type=structure_type)
            for each_monthly_payroll_template  in all_monthly_payroll_template:
                # get all the employees that are related to this career path
                employees = employee_models.Employee.objects.filter(career_path=each_monthly_payroll_template.grade_level)
                for each_employees in employees:
                    employee_generatedInstance = generated_employee_montly_structure.EmployeeSavedMonthlySalaryStructure.objects.create(
                        grade_level=each_monthly_payroll_template.grade_level,
                        gross_money=each_monthly_payroll_template.gross_money,
                        employee=each_employees,
                        generated_for=generated_for,
                        structure_type=structure_type,
                        rate=each_monthly_payroll_template.rate,
                        number_of_work=each_monthly_payroll_template.number_of_work,
                        )
                    
                    "i want to fill the data from EmployeeOtherReceivables to EmployeeSavedOtherReceivables"
                    employe_other_receivables = each_monthly_payroll_template.employeeotherreceivables_set.all()
                    for each_employe_other_receivables in employe_other_receivables:
                        generated_employee_montly_structure.EmployeeSavedOtherReceivables.objects.create(
                            monthly_salary_structure=employee_generatedInstance,
                            other_receivables_element =each_employe_other_receivables.other_receivables_element,
                            other_receivables_element_gross_percent =each_employe_other_receivables.other_receivables_element_gross_percent,
                            value  = each_employe_other_receivables.value
                        )
                        
                    
                    "i want to fill the data from EmployeeReceivables to EmployeeSavedEmployeeReceivables"
                    employeereceivables =each_monthly_payroll_template.employeereceivables_set.all()
                    for each_employeereceivables in employeereceivables:
                        generated_employee_montly_structure.EmployeeSavedEmployeeReceivables.objects.create(
                            monthly_salary_structure=employee_generatedInstance,
                            fixed_receivables_element=each_employeereceivables.fixed_receivables_element,
                            fixed_receivables_element_gross_percent=each_employeereceivables.fixed_receivables_element_gross_percent,
                            value=each_employeereceivables.value,
                        )
                    "i want to fill the data from EmployeeRegulatoryRecievables to EmployeeSavedEmployeeRegulatoryRecievables"
                    employee_regulatory_reciveable = each_monthly_payroll_template.employeeregulatoryrecievables_set.all()
                    for eachemployee_regulatory_reciveable in employee_regulatory_reciveable:
                        generated_employee_montly_structure.EmployeeSavedEmployeeRegulatoryRecievables.objects.create(
                            monthly_salary_structure=employee_generatedInstance,
                            Employee_regulatory_recievables=eachemployee_regulatory_reciveable.Employee_regulatory_recievables,
                            Employee_regulatory_recievables_gross_percent=eachemployee_regulatory_reciveable.Employee_regulatory_recievables_gross_percent,
                            regulatory_rates=eachemployee_regulatory_reciveable.regulatory_rates,
                            value=eachemployee_regulatory_reciveable.value,

                        )
                    "i want to fill the data from EmployeeRegulatoryDeductables to EmployeeSavedEmployeeRegulatoryDeductables"
                    employee_regulatory_deductable = each_monthly_payroll_template.employeeregulatorydeductables_set.all()
                    for each_employee_regulatory_deductable in employee_regulatory_deductable:
                        generated_employee_montly_structure.EmployeeSavedEmployeeRegulatoryDeductables.objects.create(
                            monthly_salary_structure=employee_generatedInstance,
                            Employee_regulatory_deductables=each_employee_regulatory_deductable.Employee_regulatory_deductables,
                            Employee_regulatory_deductables_gross_percent=each_employee_regulatory_deductable.Employee_regulatory_deductables_gross_percent,
                            regulatory_rates=each_employee_regulatory_deductable.regulatory_rates,
                            value=each_employee_regulatory_deductable.value,
                        )
                    "i want to fill the data from EmployeeOtherDeductables to EmployeeSavedEmployeeOtherDeductables"
                    employee_other_deductables = each_monthly_payroll_template.employeeotherdeductables_set.all()
                    for each_employee_other_deductables in employee_other_deductables:
                        generated_employee_montly_structure.EmployeeSavedEmployeeOtherDeductables.objects.create(
                            monthly_salary_structure=employee_generatedInstance,
                            Employee_other_deductables=each_employee_other_deductables.Employee_other_deductables,
                            Employee_other_deductables_gross_percent=each_employee_other_deductables.Employee_other_deductables_gross_percent,
                            value=each_employee_other_deductables.value,
                        )
                    
        return validated_data


class cleanGeneratedEmployeeSavedMonthlySalaryStructure(serializers.ModelSerializer):
    saved_employee_receivables = serializers.SerializerMethodField()
    saved_employee_regulatory_recievables = serializers.SerializerMethodField()
    saved_employee_other_recievables = serializers.SerializerMethodField()
    saved_employee_regulatory_deductables = serializers.SerializerMethodField()
    saved_employee_other_deductables = serializers.SerializerMethodField()
    net_salary = serializers.SerializerMethodField()
    total_gross = serializers.SerializerMethodField()
    annual_gross = serializers.SerializerMethodField()
    employee_full_name = serializers.SerializerMethodField()

    def get_employee_full_name(self,EmployeeSavedMonthlySalaryStructureInstance):
        emp = EmployeeSavedMonthlySalaryStructureInstance.employee.user
        # 
        # 
        return emp.first_name+' '+emp.last_name
    def get_net_salary(self,EmployeeSavedMonthlySalaryStructureInstance):
        "// Total Gross Minus (All Deductibles + Regulatory Receivables)"
        sum_of_regulatory = sum(generated_employee_montly_structure.EmployeeSavedEmployeeRegulatoryRecievables.objects.filter(monthly_salary_structure=EmployeeSavedMonthlySalaryStructureInstance).values_list('value',flat=True))
        sum_of_regulatory_deductables = sum(generated_employee_montly_structure.EmployeeSavedEmployeeRegulatoryDeductables.objects.filter(monthly_salary_structure=EmployeeSavedMonthlySalaryStructureInstance).values_list('value',flat=True))
        sum_of_other_deductables = sum(generated_employee_montly_structure.EmployeeSavedEmployeeOtherDeductables.objects.filter(monthly_salary_structure=EmployeeSavedMonthlySalaryStructureInstance).values_list('value',flat=True))
        total_sum = sum_of_regulatory+sum_of_regulatory_deductables+sum_of_other_deductables
        return EmployeeSavedMonthlySalaryStructureInstance.gross_money-total_sum

    def get_total_gross(self,EmployeeSavedMonthlySalaryStructureInstance):
       " // sum of all the receiveables"
       sum_of_recievable = sum(generated_employee_montly_structure.EmployeeSavedEmployeeRegulatoryRecievables.objects.filter(monthly_salary_structure=EmployeeSavedMonthlySalaryStructureInstance).values_list('value',flat=True))
       sum_of_regulatory = sum(generated_employee_montly_structure.EmployeeSavedEmployeeReceivables.objects.filter(monthly_salary_structure=EmployeeSavedMonthlySalaryStructureInstance).values_list('value',flat=True))
       return sum_of_regulatory+sum_of_recievable

    def get_annual_gross(self,EmployeeSavedMonthlySalaryStructureInstance):
        "//totalGross * 12"
        return EmployeeSavedMonthlySalaryStructureInstance.gross_money*12
    
    def get_saved_employee_other_recievables(self,EmployeeSavedMonthlySalaryStructureInstance):
        return generated_employee_montly_structure.EmployeeSavedOtherReceivables.objects.filter(monthly_salary_structure=EmployeeSavedMonthlySalaryStructureInstance).values(
            'value','other_receivables_element','other_receivables_element_gross_percent'
        )
    def get_saved_employee_receivables(self,EmployeeSavedMonthlySalaryStructureInstance):
        return generated_employee_montly_structure.EmployeeSavedEmployeeReceivables.objects.filter(monthly_salary_structure=EmployeeSavedMonthlySalaryStructureInstance).values(
            'fixed_receivables_element','fixed_receivables_element_gross_percent','value'
        )
    def get_saved_employee_regulatory_recievables(self,EmployeeSavedMonthlySalaryStructureInstance):
        return generated_employee_montly_structure.EmployeeSavedEmployeeRegulatoryRecievables.objects.filter(monthly_salary_structure=EmployeeSavedMonthlySalaryStructureInstance).values(
            'Employee_regulatory_recievables','Employee_regulatory_recievables_gross_percent','regulatory_rates',
            'value'
        )
    def get_saved_employee_regulatory_deductables(self,EmployeeSavedMonthlySalaryStructureInstance):
        return generated_employee_montly_structure.EmployeeSavedEmployeeRegulatoryDeductables.objects.filter(monthly_salary_structure=EmployeeSavedMonthlySalaryStructureInstance).values(
            'Employee_regulatory_deductables','Employee_regulatory_deductables_gross_percent','regulatory_rates',
            'value'
        )
    def get_saved_employee_other_deductables(self,EmployeeSavedMonthlySalaryStructureInstance):
        return generated_employee_montly_structure.EmployeeSavedEmployeeOtherDeductables.objects.filter(monthly_salary_structure=EmployeeSavedMonthlySalaryStructureInstance).values(
            'Employee_other_deductables','Employee_other_deductables_gross_percent','value',
        )

    class Meta:
        fields = "__all__"
        model =generated_employee_montly_structure.EmployeeSavedMonthlySalaryStructure