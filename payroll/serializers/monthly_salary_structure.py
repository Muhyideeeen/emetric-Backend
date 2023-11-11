from  rest_framework import serializers,status
from core.utils.exception import CustomValidation
from core.utils.helper_function import get_amount_by_percent
from ..models import monthly_salary_structure as models
from django.db import transaction
from career_path import models as career_path_models


class ListOfEmployeeReceivablesSerializer(serializers.Serializer):
    fixed_receivables_element= serializers.CharField()
    fixed_receivables_element_gross_percent= serializers.IntegerField()

class ListOfEmployeeOtherReceivablesSerializer(serializers.Serializer):
    other_receivables_element = serializers.CharField()
    other_receivables_element_gross_percent = serializers.IntegerField()
class ListOfEmployeeRegulatoryRecievablesSerializer(serializers.Serializer):
    regulatory_receivables= serializers.CharField()
    regulatory_receivables_gross_percent= serializers.IntegerField()
    regulatory_rates = serializers.IntegerField()

class ListOfEmployeeRegulatoryDeductablesSerializer(serializers.Serializer):
    regulatory_deductables= serializers.CharField()
    regulatory_deductables_gross_percent =serializers.IntegerField()
    regulatory_rates = serializers.IntegerField()

class ListOfEmployeeOtherDeductablesSerializer(serializers.Serializer):
    other_deductables= serializers.CharField()
    other_deductables_gross_percent =serializers.IntegerField()

class MonthSalaryStructureCreationSerializer(serializers.Serializer):
    "struture Style"
    structure_type = serializers.ChoiceField(choices=['monthly','daily','hourly'])
    rate =serializers.DecimalField(required=False,max_digits=20, decimal_places=2)
    number_of_work = serializers.IntegerField(required=False)
    
    grade_level = serializers.CharField()
    gross_money = serializers.DecimalField(max_digits=20, decimal_places=2)
    "Receivables"
    employee_receivables = ListOfEmployeeReceivablesSerializer(many=True)
    employee_regulatory_recievables =ListOfEmployeeRegulatoryRecievablesSerializer(many=True)
    employee_other_receivables  = ListOfEmployeeOtherReceivablesSerializer(many=True)

    "Deductables"
    employee_regulatory_deductables = ListOfEmployeeRegulatoryDeductablesSerializer(many=True)
    employee_other_deductables = ListOfEmployeeOtherDeductablesSerializer(many=True)


    def validate(self, attrs):
        structure_type = attrs.get('structure_type',None)
        rate=attrs.get('rate',None)
        number_of_work=attrs.get('number_of_work',None)

        if structure_type =='daily' or structure_type =='hourly':
            if rate is None:raise CustomValidation(
            detail=f'Rate  is required for {structure_type}',field='error',status_code=status.HTTP_400_BAD_REQUEST
            )
            if number_of_work is None:raise CustomValidation(
            detail=f'Number of work required for {structure_type}',field='error',status_code=status.HTTP_400_BAD_REQUEST
            )

        if not  self._validate_gross_percent(attrs): raise CustomValidation(
            detail='Total gross is ment to be 100%',field='error',status_code=status.HTTP_400_BAD_REQUEST
        )
        if not  career_path_models.CareerPath.objects.filter(career_path_id=attrs.get('grade_level')).exists():
            raise CustomValidation(detail='this level does not exist',field='grade_level',status_code=status.HTTP_400_BAD_REQUEST)
        else:
            'check if this career path exist in monthly payroll'
            career_path  = career_path_models.CareerPath.objects.get(career_path_id=attrs.get('grade_level'))
            if models.MonthlySalaryStructure.objects.filter(grade_level=career_path,structure_type=structure_type).exists():
                raise CustomValidation(detail='This level already has a Monthly Salary Payroll Strcuture',field='grade_level',status_code=status.HTTP_400_BAD_REQUEST)

        return super().validate(attrs)




    def _validate_gross_percent(self,attrs):

        def get_other_receivable_gross_percent(each_item):
            return each_item.get('other_receivables_element_gross_percent',0)
        def getfixed_receivables_element_gross_percent(each_item):
            return each_item.get('fixed_receivables_element_gross_percent',0)
        def getregulatory_receivables_gross_percent(each_item):
            return each_item.get('regulatory_receivables_gross_percent',0)
        def getregulatory_deductables_gross_percent(each_item):
            return each_item.get('regulatory_deductables_gross_percent',0)
        def getother_deductables_gross_percent(each_item):
            return each_item.get('other_deductables_gross_percent',0)

        "this validate if all the gross Receivables percent sum up to 100"

        list_of_gross = [
            sum(map(getfixed_receivables_element_gross_percent,attrs.get('employee_receivables'))),
            sum(map(getregulatory_receivables_gross_percent,attrs.get('employee_regulatory_recievables'))),
            sum(map(get_other_receivable_gross_percent,attrs.get('employee_other_receivables')))
            # sum(map(getregulatory_deductables_gross_percent,attrs.get('employee_regulatory_deductables'))),
            # sum(map(getother_deductables_gross_percent,attrs.get('employee_other_deductables'))),
        ]
        return sum(list_of_gross) ==100



    def create(self, validated_data):
        structure_type = validated_data.get('structure_type',None)
        rate=validated_data.get('rate',None)
        number_of_work=validated_data.get('number_of_work',None)
        grade_level = validated_data.get('grade_level')
        gross_money = validated_data.get('gross_money')
        employee_receivables = validated_data.get('employee_receivables',[])
        employee_regulatory_recievables = validated_data.get('employee_regulatory_recievables',[])
        employee_regulatory_deductables = validated_data.get('employee_regulatory_deductables',[])
        employee_other_deductables = validated_data.get('employee_other_deductables',[])
        employee_other_receivables= validated_data.get('employee_other_receivables',[])
        carer_path = career_path_models.CareerPath.objects.get(career_path_id=grade_level)
        "first we need to create MonthlySalaryStructure"
        monthlysalarystructureinstance = models.MonthlySalaryStructure.objects.create(
            grade_level=carer_path,
            gross_money=gross_money,
        )
        if structure_type =='daily' or structure_type =='hourly':
            monthlysalarystructureinstance.structure_type=structure_type
            monthlysalarystructureinstance.rate=rate
            monthlysalarystructureinstance.number_of_work=number_of_work
            monthlysalarystructureinstance.gross_money = monthlysalarystructureinstance.cal_gross_money()
            monthlysalarystructureinstance.save()
        "bulk create receivables "
        self.bulkCreateEmployeeReceivables(monthlysalarystructureinstance,employee_receivables)
        self.bulkCreateEmployeeRegulatoryRecievables(monthlysalarystructureinstance,employee_regulatory_recievables)
        self.bulkCreateEmployeeOtherReceivable(monthlysalarystructureinstance,employee_other_receivables)
        "bulk create deductables"
        self.bulkCreateEmployeeRegulatoryDeductable(monthlysalarystructureinstance,employee_regulatory_deductables)
        self.bulkCreateEmployeeOtherDeductables(monthlysalarystructureinstance,employee_other_deductables)
        return monthlysalarystructureinstance


    def bulkCreateEmployeeOtherReceivable(self,monthlysalarystructureinstance,employee_other_receivables:list):
        with transaction.atomic():
            for data in employee_other_receivables:
                instance= models.EmployeeOtherReceivables(
                    monthly_salary_structure=monthlysalarystructureinstance,
                    other_receivables_element=data.get('other_receivables_element','null'),
                    other_receivables_element_gross_percent=data.get('other_receivables_element_gross_percent',0),
                    value=get_amount_by_percent(
                        data.get('other_receivables_element_gross_percent',0),monthlysalarystructureinstance.gross_money
                    )
                )
                instance.save()
    def bulkCreateEmployeeReceivables(self,monthlysalarystructureinstance,employee_receivables:list):
        with transaction.atomic():
            for data in employee_receivables:
                instance = models.EmployeeReceivables(
                    monthly_salary_structure=monthlysalarystructureinstance,
                    fixed_receivables_element=data.get('fixed_receivables_element','null'),
                    fixed_receivables_element_gross_percent=data.get('fixed_receivables_element_gross_percent',0),
                    value = get_amount_by_percent(
                        data.get('fixed_receivables_element_gross_percent',0),monthlysalarystructureinstance.gross_money)
                )
                instance.save()

    def bulkCreateEmployeeRegulatoryRecievables(self,monthlysalarystructureinstance,employee_regulatory_recievables:list):
        
        with transaction.atomic():
            for data in employee_regulatory_recievables:
                instance = models.EmployeeRegulatoryRecievables(
                    monthly_salary_structure=monthlysalarystructureinstance,
                    Employee_regulatory_recievables=data.get('regulatory_receivables',"null"),
                    Employee_regulatory_recievables_gross_percent=data.get('regulatory_receivables_gross_percent',0.00),
                    regulatory_rates=data.get('regulatory_rates',0.00),
                    value = get_amount_by_percent(
                        data.get('regulatory_receivables_gross_percent',0),monthlysalarystructureinstance.gross_money)
                )
                instance.save()


    def bulkCreateEmployeeRegulatoryDeductable(self,monthlysalarystructureinstance,employee_regulatory_deductables:list):
            with transaction.atomic():
                for data in employee_regulatory_deductables:
                    instance = models.EmployeeRegulatoryDeductables(
                        monthly_salary_structure=monthlysalarystructureinstance,
                        Employee_regulatory_deductables=data.get('regulatory_deductables','null'),  
                        Employee_regulatory_deductables_gross_percent=data.get('regulatory_deductables_gross_percent',0.00),         
                        regulatory_rates=data.get('regulatory_rates',0.00),
                        value = get_amount_by_percent(
                        data.get('regulatory_deductables_gross_percent',0),monthlysalarystructureinstance.gross_money)
                    )
                    instance.save()


    def bulkCreateEmployeeOtherDeductables(self,monthlysalarystructureinstance,employee_other_deductables:list):
        with transaction.atomic():
            for data in employee_other_deductables:
                instance = models.EmployeeOtherDeductables(
                        monthly_salary_structure=monthlysalarystructureinstance,
                        Employee_other_deductables= data.get('other_deductables',"null"),
                        Employee_other_deductables_gross_percent=data.get('other_deductables_gross_percent',0.00),
                        value = get_amount_by_percent(
                        data.get('other_deductables_gross_percent',0),monthlysalarystructureinstance.gross_money)
                )
                instance.save()




class  MonthSalaryStructureCleanerSerializer(serializers.ModelSerializer):

    employee_receivables = serializers.SerializerMethodField()
    employee_regulatory_recievables = serializers.SerializerMethodField()
    employee_regulatory_deductables = serializers.SerializerMethodField()
    employee_other_deductables = serializers.SerializerMethodField()
    employee_other_receivables = serializers.SerializerMethodField()


    def get_employee_other_receivables(self,MonthlySalaryInstance):
        return models.EmployeeOtherReceivables.objects.filter(monthly_salary_structure=MonthlySalaryInstance).values(
            'other_receivables_element',
            'other_receivables_element_gross_percent','value')
    def get_employee_receivables(self,MonthlySalaryInstance):
        return models.EmployeeReceivables.objects.filter(monthly_salary_structure=MonthlySalaryInstance).values(
            'fixed_receivables_element','fixed_receivables_element_gross_percent','value'
        )

    def get_employee_regulatory_recievables(self,MonthlySalaryInstance):
        return models.EmployeeRegulatoryRecievables.objects.filter(monthly_salary_structure=MonthlySalaryInstance).values(
            'Employee_regulatory_recievables','Employee_regulatory_recievables_gross_percent','regulatory_rates',
            'value'
        )

    def get_employee_regulatory_deductables(self,MonthlySalaryInstance):
        return models.EmployeeRegulatoryDeductables.objects.filter(monthly_salary_structure=MonthlySalaryInstance).values(
            'Employee_regulatory_deductables','Employee_regulatory_deductables_gross_percent','regulatory_rates',
            'value'
        )

    def get_employee_other_deductables(self,MonthlySalaryInstance):
        return models.EmployeeOtherDeductables.objects.filter(monthly_salary_structure=MonthlySalaryInstance).values(
            'Employee_other_deductables','Employee_other_deductables_gross_percent','value',
        )
    class Meta:
        fields = "__all__"
        model = models.MonthlySalaryStructure