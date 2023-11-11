from django.db import models
from employee import models as employee_models
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from core.utils.validators import validate_file_extension_for_pdf


BASE_FILE_PATH = "leave_files_upload/"


class Leave(models.Model):
    "this models can only be created or managed by the hr_admin"
    class LeaveType(models.TextChoices):
        annual = 'annual'
        sick = 'sick'
        maternity ='maternity'
        paternity='paternity'
        bereavement='bereavement'
        compensatory ='compensatory'
        sabbatical ='sabbatical'
    leave_choice = models.CharField(max_length=100,choices=LeaveType.choices, unique=False,)
    duration = models.IntegerField()# this is in days
    leave_allowance = models.DecimalField(max_digits=20, decimal_places=2)
    leave_formula=  models.CharField(max_length=3)
    grade_level = models.IntegerField( )


    def __str__(self) -> str:
        return f'{self.leave_choice} for GradeLevel:{self.grade_level}'



class EmployeeLeaveApplication(models.Model):
    remark = models.TextField(default='')
    deputizing_officer = models.TextField(default='')
    recorded_duration = models.IntegerField(default=0)
    hand_over_report =models.FileField(
        upload_to=(BASE_FILE_PATH),
        db_index=True,
        null=True,
        validators=[validate_file_extension_for_pdf],
        storage=RawMediaCloudinaryStorage(),
    )
    employee = models.ForeignKey(employee_models.Employee,on_delete=models.CASCADE)
    leave_type = models.ForeignKey(Leave,on_delete=models.SET_NULL,null=True)#type of leave the employee is applying for 
    recorded_allowance =models.DecimalField(max_digits=20, decimal_places=2) # this allowance will be recorded after the hr and team lead has approved so in the future we can know how much this employee recived for the leave 
    start_date = models.DateField()
    # added null to it cus i added it late
    end_date = models.DateField(null=True,default=None)
    # this will be filled by the backend guy 
    start_time= models.TimeField()# this should start from 12:00 am
    end_time = models.TimeField()#this will end on 11:00pm
    # is_team_lead_can_see would be set to true once the instance is created
    is_team_lead_can_see = models.BooleanField(default=True)
    class ApplicationApprove(models.TextChoices):
        approved='approved'
        disapproved='disapproved'
        request_a_new_date ='request_a_new_date'
        pending = 'pending'
    team_lead_approve = models.CharField(max_length=100,choices=ApplicationApprove.choices,default=ApplicationApprove.pending)
    # is_hradmin_can_see would be set to true once the team_lead_approve True

    is_hradmin_can_see = models.BooleanField(default=False)
    hradmin_lead_approve = models.CharField(max_length=100,choices=ApplicationApprove.choices,default=ApplicationApprove.pending)


    def __str__(self) -> str:
        return f'Employee:{self.employee} Applied for application'
