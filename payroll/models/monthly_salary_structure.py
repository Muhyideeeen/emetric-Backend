from django.db import models
from career_path import models as careerpath_models 

# Create your models here.
"""
#Note

I made a mistake MonthlySalaryStructure does not mean just for month it has been modifyied into a SalaryStructure 
because is works wth monthly daily and  hourly
"""

class  MonthlySalaryStructure(models.Model):
    """
    MonthlySalaryStructure is a template of how the EmployeeSavedMonthlySalaryStructure will look like
    """
    class SalaryStructureType(models.TextChoices):
        monthly = 'monthly'
        daily = 'daily'
        hourly = 'hourly'
    grade_level = models.ForeignKey(careerpath_models.CareerPath,on_delete=models.CASCADE)
    gross_money =models.DecimalField(max_digits=20, decimal_places=2,default=0.00)

    structure_type = models.CharField(max_length=12,choices=SalaryStructureType.choices,default=SalaryStructureType.monthly)
    # created_at = models.DateTimeField(auto_now_add=True)
    "depending"
    rate = models.DecimalField(max_digits=20, decimal_places=2,default=0.00,blank=True)
    number_of_work = models.IntegerField(default=0,blank=True)


    def cal_gross_money(self,):
        'rate multiplied by number_of_work we get the gross'
        return self.rate * self.number_of_work

    def __str__(self):
        return f'MonthlySalaryStructure for {self.grade_level.level}'



class EmployeeReceivables(models.Model):
    monthly_salary_structure = models.ForeignKey(MonthlySalaryStructure,on_delete=models.CASCADE) 
    fixed_receivables_element = models.TextField(default='')
    fixed_receivables_element_gross_percent = models.IntegerField()
    # this value would be fill in the stage when we trying to generate the spread
    # this value must not surpass the gross percent
    value  = models.DecimalField(max_digits=20, decimal_places=2,default=0.00)

    def __str__(self):
        return f'fixed_receivables_element:{self.fixed_receivables_element}'
class EmployeeOtherReceivables(models.Model):
    monthly_salary_structure = models.ForeignKey(MonthlySalaryStructure,on_delete=models.CASCADE) 
    other_receivables_element = models.TextField(default='')
    other_receivables_element_gross_percent = models.IntegerField()
    value  = models.DecimalField(max_digits=20, decimal_places=2,default=0.00)

    def __str__(self):return f'other_receivables_element:{self.other_receivables_element}'



class EmployeeRegulatoryRecievables(models.Model):
    monthly_salary_structure = models.ForeignKey(MonthlySalaryStructure,on_delete=models.CASCADE) 
    Employee_regulatory_recievables = models.TextField(default='')
    Employee_regulatory_recievables_gross_percent = models.IntegerField()
    regulatory_rates  = models.IntegerField()
    # this value would be fill in the stage when we trying to generate the spread
    # this value must not surpass the gross percent
    value  = models.DecimalField(max_digits=20, decimal_places=2,default=0.00)

    def __str__(self):
        return f'Employee_regulatory_recievables:{self.Employee_regulatory_recievables}'

class EmployeeRegulatoryDeductables(models.Model):
    monthly_salary_structure = models.ForeignKey(MonthlySalaryStructure,on_delete=models.CASCADE) 
    Employee_regulatory_deductables = models.TextField(default='')
    Employee_regulatory_deductables_gross_percent = models.IntegerField()
    regulatory_rates  = models.IntegerField()
    # this value is just reducing the total_gross 
    value  = models.DecimalField(max_digits=20, decimal_places=2,default=0.00)


    def __str__(self):
        return f'Employee_regulatory_deductables:{self.Employee_regulatory_deductables}'


class EmployeeOtherDeductables(models.Model):
    monthly_salary_structure = models.ForeignKey(MonthlySalaryStructure,on_delete=models.CASCADE) 
    Employee_other_deductables = models.TextField(default='')
    Employee_other_deductables_gross_percent = models.IntegerField()
    value  = models.DecimalField(max_digits=20, decimal_places=2,default=0.00)
    def __str__(self):
        return f'Employee_other_deductables:{self.Employee_other_deductables}'


