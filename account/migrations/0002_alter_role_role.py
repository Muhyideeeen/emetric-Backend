# Generated by Django 3.2.16 on 2022-10-20 03:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='role',
            field=models.CharField(choices=[('employee', 'Employee'), ('team_lead', 'Team Lead'), ('admin', 'Admin'), ('admin_hr', 'Admin HR'), ('super_admin', 'Super Admin'), ('Exco_or_Management', 'Exco/Management'), ('Committee_Member', 'Committee Member'), ('Committee_Chair', 'Committee Chair')], max_length=25),
        ),
    ]
