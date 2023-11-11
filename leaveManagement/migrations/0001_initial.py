# Generated by Django 3.2.13 on 2022-10-18 09:11

import cloudinary_storage.storage
import core.utils.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employee', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Leave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leave_choice', models.CharField(choices=[('annual', 'Annual'), ('sick', 'Sick'), ('maternity', 'Maternity'), ('paternity', 'Paternity'), ('bereavement', 'Bereavement'), ('compensatory', 'Compensatory'), ('sabbatical', 'Sabbatical')], max_length=100)),
                ('duration', models.IntegerField()),
                ('leave_allowance', models.DecimalField(decimal_places=2, max_digits=20)),
                ('leave_formula', models.CharField(max_length=3)),
                ('grade_level', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeLeaveApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remark', models.TextField(default='')),
                ('deputizing_officer', models.TextField(default='')),
                ('recorded_duration', models.IntegerField(default=0)),
                ('hand_over_report', models.FileField(db_index=True, null=True, storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(), upload_to='leave_files_upload/', validators=[core.utils.validators.validate_file_extension_for_pdf])),
                ('recorded_allowance', models.DecimalField(decimal_places=2, max_digits=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(default=None, null=True)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('is_team_lead_can_see', models.BooleanField(default=True)),
                ('team_lead_approve', models.CharField(choices=[('approved', 'Approved'), ('disapproved', 'Disapproved'), ('request_a_new_date', 'Request A New Date'), ('pending', 'Pending')], default='pending', max_length=100)),
                ('is_hradmin_can_see', models.BooleanField(default=False)),
                ('hradmin_lead_approve', models.CharField(choices=[('approved', 'Approved'), ('disapproved', 'Disapproved'), ('request_a_new_date', 'Request A New Date'), ('pending', 'Pending')], default='pending', max_length=100)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employee.employee')),
                ('leave_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='leaveManagement.leave')),
            ],
        ),
    ]
