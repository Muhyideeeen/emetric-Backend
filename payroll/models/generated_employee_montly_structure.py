from django.db import models
from career_path import models as careerpath_models 
from employee import models as employee_models

# Create your models here.

"""
steps to generate

    click on genreate
    get alll monlty payroll template
    for each of the template use the career path to filter the employee
    for each of the employee create  a EmployeeSavedMonthlySalaryStructure


how to get generated data 
    we first send all the available date to the front end so they can query a generated data for that time
"""
class  EmployeeSavedMonthlySalaryStructure(models.Model):
    """
    MonthlySalaryStructure is a template of how the EmployeeSavedMonthlySalaryStructure will look like
    once a hr generate a pay roll using MonthlySalaryStructure this is the model that will save all the information and link it to the employee
     """
    class SalaryStructureType(models.TextChoices):
        monthly = 'monthly'
        daily = 'daily'
        hourly = 'hourly'
    grade_level = models.ForeignKey(careerpath_models.CareerPath,on_delete=models.CASCADE)
    gross_money =models.DecimalField(max_digits=20, decimal_places=2)
    # created_at = models.DateTimeField(auto_now_add=True)
    employee = models.ForeignKey(employee_models.Employee,null=True,on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    generated_for = models.DateField()# this will act as pagination for the front end
    updated_at = models.DateTimeField(auto_now=True)


    structure_type = models.CharField(max_length=12,choices=SalaryStructureType.choices,default=SalaryStructureType.monthly)
    # created_at = models.DateTimeField(auto_now_add=True)
    "depending"
    rate = models.DecimalField(max_digits=20, decimal_places=2,default=0.00,blank=True)
    number_of_work = models.IntegerField(default=0,blank=True)

    def __str__(self):
        return f'EmployeeSavedMonthlySalaryStructure for {self.grade_level.level}'

class EmployeeSavedOtherReceivables(models.Model):
    monthly_salary_structure = models.ForeignKey(EmployeeSavedMonthlySalaryStructure,on_delete=models.CASCADE) 
    other_receivables_element = models.TextField(default='')
    other_receivables_element_gross_percent = models.IntegerField()
    value  = models.DecimalField(max_digits=20, decimal_places=2,default=0.00)

    def __str__(self):return f'other_receivables_element:{self.other_receivables_element}'


class EmployeeSavedEmployeeReceivables(models.Model):
    monthly_salary_structure = models.ForeignKey(EmployeeSavedMonthlySalaryStructure,on_delete=models.CASCADE) 
    fixed_receivables_element = models.TextField(default='')
    fixed_receivables_element_gross_percent = models.IntegerField()
    # this value would be fill in the stage when we trying to generate the spread
    # this value must not surpass the gross percent
    value  = models.DecimalField(max_digits=20, decimal_places=2,default=0.00)

    def __str__(self):
        return f'fixed_receivables_element:{self.fixed_receivables_element}'



class EmployeeSavedEmployeeRegulatoryRecievables(models.Model):
    monthly_salary_structure = models.ForeignKey(EmployeeSavedMonthlySalaryStructure,on_delete=models.CASCADE) 
    Employee_regulatory_recievables = models.TextField(default='')
    Employee_regulatory_recievables_gross_percent = models.IntegerField()
    regulatory_rates  = models.IntegerField()
    # this value would be fill in the stage when we trying to generate the spread
    # this value must not surpass the gross percent
    value  = models.DecimalField(max_digits=20, decimal_places=2,default=0.00)

    def __str__(self):
        return f'Employee_regulatory_recievables:{self.Employee_regulatory_recievables}'

class EmployeeSavedEmployeeRegulatoryDeductables(models.Model):
    monthly_salary_structure = models.ForeignKey(EmployeeSavedMonthlySalaryStructure,on_delete=models.CASCADE) 
    Employee_regulatory_deductables = models.TextField(default='')
    Employee_regulatory_deductables_gross_percent = models.IntegerField()
    regulatory_rates  = models.IntegerField()
    # this value is just reducing the total_gross 
    value  = models.DecimalField(max_digits=20, decimal_places=2,default=0.00)


    def __str__(self):
        return f'Employee_regulatory_deductables:{self.Employee_regulatory_deductables}'


class EmployeeSavedEmployeeOtherDeductables(models.Model):
    monthly_salary_structure = models.ForeignKey(EmployeeSavedMonthlySalaryStructure,on_delete=models.CASCADE) 
    Employee_other_deductables = models.TextField(default='')
    Employee_other_deductables_gross_percent = models.IntegerField()
    value  = models.DecimalField(max_digits=20, decimal_places=2,default=0.00)
    def __str__(self):
        return f'Employee_other_deductables:{self.Employee_other_deductables}'

