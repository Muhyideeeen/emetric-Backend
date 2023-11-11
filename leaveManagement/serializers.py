from django.db import IntegrityError
from rest_framework import serializers
from . import models
from core.utils import CustomValidation,permissions
from employee import models as emp_models 
from account.models import Role
from career_path import models as career_path_models




class AdminLeaveManagementSerializer(serializers.ModelSerializer):


    def create(self, validated_data):
        grade_level = validated_data.get('grade_level',)
        leave_choice = validated_data.get('leave_choice',)
        leave_allowance = validated_data.get('leave_allowance')
        leave_formula = validated_data.get('leave_formula')
        duration = validated_data.get('duration')

        "check if this data should be created for all leave"
        for_all_level = self.context.get('for_all_level',None)
        if for_all_level:
            # get arrays of the career path level

            all_levels_in_careerPath = list(career_path_models.CareerPath.objects.all().values('level'))
            for level in all_levels_in_careerPath:
                if models.Leave.objects.filter(grade_level=level.get('level'),leave_choice=leave_choice).exists():
                    pass
                else:
                    validated_data['grade_level'] = level.get('level')
                    super().create(validated_data)
            # loopthrough them and create a leave using get or create(grade_level=level_id,leave_choice= )
            return {}
        else:
        # if there i a grade_level and leave choice exist 
            if models.Leave.objects.filter(grade_level=grade_level,leave_choice=leave_choice).exists():raise CustomValidation(
                detail='Leave with the grade level already exist',field='grade_level',status_code=400
            )
            return super().create(validated_data)

    class Meta:
        model = models.Leave
        fields = [
            'leave_choice','duration','leave_allowance',
            'leave_formula','grade_level','id'
        ]
        read_only_fields = ['id']
        
class EmployeeLeaveApplicationSerializer(serializers.Serializer):
    "employee will apply for a leave with this serializer"
    leave_type_id = serializers.IntegerField()
    recorded_allowance = serializers.DecimalField(max_digits=20, decimal_places=2)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    deputizing_officer  = serializers.CharField()
    hand_over_report = serializers.FileField()


    def validate(self, attrs):
        leave_type_id = attrs.get('leave_type_id',None)
        user_role =self.context.get('request').user.user_role.role
        print({'user_role':user_role})
        if not user_role in [Role.EMPLOYEE,Role.TEAM_LEAD]:
            raise  CustomValidation(
            detail='You are not an employee ',field='Permission',status_code=400
        )
        if leave_type_id:
            if not  models.Leave.objects.filter(id=leave_type_id):
                raise CustomValidation(
            detail='Invalid Id ',field='leave_type_id',status_code=400)
        return super().validate(attrs)
    def create(self, validated_data):
        ''
        loggedInUser = self.context.get('request').user
        employee = emp_models.Employee.objects.get(user__email=loggedInUser.email)
        leave = models.Leave.objects.get(id=validated_data.get('leave_type_id'))
        deputizing_officer = validated_data.get('deputizing_officer')
        hand_over_report =  validated_data.get('hand_over_report')
        if employee.career_path:
            if employee.career_path.level!=leave.grade_level:
                'if employee career path is not same with grade_level'
                raise CustomValidation(detail='This leave is not meant for your grade level',field='grade_level',status_code=400)
        else:
            "this means the user does not have careerpath"
            raise CustomValidation(detail='You dont have a grade level ask your hr admin to add you to a level',field='grade_level',status_code=400)

        leave_application = models.EmployeeLeaveApplication.objects.create(
            employee=employee,
            leave_type = leave,
            recorded_allowance = leave.leave_allowance,
            start_date = validated_data.get('start_date'),
            end_date = validated_data.get('end_date'),
            start_time = '08:00',
            end_time='23:00',
            deputizing_officer=deputizing_officer,
            # "we just saving the duration for feature use"
            recorded_duration = leave.duration,
            hand_over_report=hand_over_report
        )
        
        leave_application.save()
        return leave_application

    # class Meta:   
    #     model  = models.EmployeeLeaveApplication
    #     fields = [
    #         'leave_type',
    #         'recorded_allowance',
    #         'start_date',
    #         'start_date',
    #         'end_date',
    #         'start_time',
    #         'end_time',
    #         'is_team_lead_can_see','team_lead_approve',
    #         'is_hradmin_can_see',
    #         'hradmin_lead_approve',
    #         'employee',
    #     ]
    #     read_only_fields =[
    #         'recorded_allowance',
    #          'start_time',
    #         'end_time',
    #         'employee',
    #     ]

class LeaveApplicationSerializerCleaner(serializers.ModelSerializer):
        leave_type = serializers.SerializerMethodField()

        def get_leave_type(self,instance):
            return {
                'id':instance.leave_type.id,
                'leave_choice':instance.leave_type.leave_choice,
                'duration':instance.leave_type.duration,
                'leave_formula':instance.leave_type.leave_formula,
                'grade_level':instance.leave_type.grade_level,
                'leave_allowance':instance.leave_type.leave_allowance,
            }
        class Meta:   
            model  = models.EmployeeLeaveApplication
            fields = [
                'leave_type','recorded_allowance','start_date','start_date','end_date',
                'is_team_lead_can_see','team_lead_approve',
                'is_hradmin_can_see',
                'hradmin_lead_approve',
                'employee','id','remark','deputizing_officer','recorded_duration',
                'hand_over_report'
            ]
            read_only_fields=fields



class TeamLeadReviewApplicationSerializer(serializers.Serializer):
    team_lead_approve_status =serializers.ChoiceField(choices=models.EmployeeLeaveApplication.ApplicationApprove.choices)
    leave_application_id = serializers.IntegerField()
    remark  = serializers.CharField()
    def validate(self, attrs):
        leave_application_id = attrs.get('leave_application_id',None)
        if leave_application_id:
            if not models.EmployeeLeaveApplication.objects.filter(id=leave_application_id).exists():
                raise CustomValidation(detail='This application does not exist',field='leave_application_id',status_code=400)
        
        return super().validate(attrs)

    def create(self, validated_data):
        leave_application_id = validated_data.get('leave_application_id')
        leave_application = models.EmployeeLeaveApplication.objects.get(id=leave_application_id)


        if leave_application.team_lead_approve=='approved' or  leave_application.team_lead_approve =='disapproved':
            'if team lead has choose approved or disapproved just he can change is'
            raise CustomValidation(detail="You can't change a approved or disaproved application",
            field='team_lead_approve_status',status_code=400
            )
        "we need to validate if this team lead really belongs to the same team the employee is from"
        logged_in_user = self.context.get('request').user
        team_lead_profile = emp_models.Employee.objects.get(user__email=logged_in_user.email)
        # employee_that_submitted_leave =  emp_models.Employee.objects.get(user__id=)
        
        if not permissions.is_same_team(team_lead_profile,leave_application.employee):
            raise  CustomValidation(detail='This application does not belong to your team',field='leave_application_id',status_code=400)

        
        team_lead_approve_status = validated_data.get('team_lead_approve_status')
        leave_application.remark = validated_data.get('remark', leave_application.remark)

        if team_lead_approve_status=='approved':
            leave_application.team_lead_approve='approved'
            leave_application.is_hradmin_can_see=True
            leave_application.hradmin_lead_approve='pending'

        if team_lead_approve_status == 'disapproved':
            leave_application.team_lead_approve='disapproved'
            # we want to send the data so the team lead wont see the request
            leave_application.is_team_lead_can_see=False
        
        if team_lead_approve_status == 'request_a_new_date':
            leave_application.team_lead_approve = 'request_a_new_date'
        
        leave_application.save()

        return leave_application




class HRAdminReviewApplicationSerializer(serializers.Serializer):
    hr_admin_approve_status =serializers.ChoiceField(choices=models.EmployeeLeaveApplication.ApplicationApprove.choices)
    leave_application_id = serializers.IntegerField()


    def validate(self, attrs):
        leave_application_id = attrs.get('leave_application_id',None)
        if leave_application_id:
            if not models.EmployeeLeaveApplication.objects.filter(id=leave_application_id).exists():
                raise CustomValidation(detail='This application does not exist',field='leave_application_id',status_code=400)
        return super().validate(attrs)


    def create(self, validated_data):
        leave_application_id = validated_data.get('leave_application_id')
        leave_application = models.EmployeeLeaveApplication.objects.get(id=leave_application_id)

        "this person is an hr admin so he can do approve stuff we have already validated fromt the view set level"

        hr_admin_approve_status= validated_data.get('hr_admin_approve_status')
        if hr_admin_approve_status=='approved':
            leave_application.hradmin_lead_approve='approved'
            "we trigger celery to keep track of the leave => like starting and ending a leave"
        
        if hr_admin_approve_status=='disapproved':
            leave_application.hradmin_lead_approve='disapproved'

 
        if hr_admin_approve_status=='request_a_new_date':
            leave_application.hradmin_lead_approve='request_a_new_date'

        leave_application.save()

        return leave_application

        

