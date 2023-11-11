from django.contrib import admin
from .models import monthly_salary_structure as models
from .models import generated_employee_montly_structure as gen_models
# Register your models here.




class  EmployeeRegulatoryRecievablesAdmin(admin.TabularInline):
    model = models.EmployeeRegulatoryRecievables
    extra: int=0
class  EmployeeOtherRecievablesAdmin(admin.TabularInline):
    model = models.EmployeeOtherReceivables
    extra: int=0
class  EmployeeReceivablesAdmin(admin.TabularInline):
    model = models.EmployeeReceivables
    extra: int=0
class  EmployeeRegulatoryDeductablesAdmin(admin.TabularInline):
    model = models.EmployeeRegulatoryDeductables
    extra: int=0
class  EmployeeOtherDeductablesAdmin(admin.TabularInline):
    model = models.EmployeeOtherDeductables
    extra: int=0
class MonthlySalaryStructureAdmin(admin.ModelAdmin):
   inlines = [
    EmployeeRegulatoryRecievablesAdmin,EmployeeReceivablesAdmin,
    EmployeeRegulatoryDeductablesAdmin,EmployeeOtherDeductablesAdmin,EmployeeOtherRecievablesAdmin
   ]
# admin.site.register(models.Publication,PublicationAdmin)
admin.site.register(models.MonthlySalaryStructure,MonthlySalaryStructureAdmin)



class  EmployeeSavedEmployeeRegulatoryRecievablesAdmin(admin.TabularInline):
    model = gen_models.EmployeeSavedEmployeeRegulatoryRecievables
    extra: int=0
class  EmployeeSavedEmployeeReceivablesAdmin(admin.TabularInline):
    model = gen_models.EmployeeSavedEmployeeReceivables
    extra: int=0
class  EmployeeSavedEmployeeRegulatoryDeductablesAdmin(admin.TabularInline):
    model = gen_models.EmployeeSavedEmployeeRegulatoryDeductables
    extra: int=0
class  EmployeeSavedEmployeeOtherDeductablesAdmin(admin.TabularInline):
    model = gen_models.EmployeeSavedEmployeeOtherDeductables
    extra: int=0
class EmployeeSavedMonthlySalaryStructureAdmin(admin.ModelAdmin):
   inlines = [
    EmployeeSavedEmployeeRegulatoryRecievablesAdmin,EmployeeSavedEmployeeReceivablesAdmin,
    EmployeeSavedEmployeeRegulatoryDeductablesAdmin,EmployeeSavedEmployeeOtherDeductablesAdmin
   ]
# admin.site.register(models.Publication,PublicationAdmin)
admin.site.register(gen_models.EmployeeSavedMonthlySalaryStructure,EmployeeSavedMonthlySalaryStructureAdmin)
