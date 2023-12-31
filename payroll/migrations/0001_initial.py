# Generated by Django 3.2.13 on 2022-10-18 09:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employee', '0001_initial'),
        ('career_path', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeSavedMonthlySalaryStructure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gross_money', models.DecimalField(decimal_places=2, max_digits=20)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('generated_for', models.DateField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('structure_type', models.CharField(choices=[('monthly', 'Monthly'), ('daily', 'Daily'), ('hourly', 'Hourly')], default='monthly', max_length=12)),
                ('rate', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=20)),
                ('number_of_work', models.IntegerField(blank=True, default=0)),
                ('employee', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='employee.employee')),
                ('grade_level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='career_path.careerpath')),
            ],
        ),
        migrations.CreateModel(
            name='MonthlySalaryStructure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gross_money', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('structure_type', models.CharField(choices=[('monthly', 'Monthly'), ('daily', 'Daily'), ('hourly', 'Hourly')], default='monthly', max_length=12)),
                ('rate', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=20)),
                ('number_of_work', models.IntegerField(blank=True, default=0)),
                ('grade_level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='career_path.careerpath')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeSavedOtherReceivables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('other_receivables_element', models.TextField(default='')),
                ('other_receivables_element_gross_percent', models.IntegerField()),
                ('value', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('monthly_salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.employeesavedmonthlysalarystructure')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeSavedEmployeeRegulatoryRecievables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Employee_regulatory_recievables', models.TextField(default='')),
                ('Employee_regulatory_recievables_gross_percent', models.IntegerField()),
                ('regulatory_rates', models.IntegerField()),
                ('value', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('monthly_salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.employeesavedmonthlysalarystructure')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeSavedEmployeeRegulatoryDeductables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Employee_regulatory_deductables', models.TextField(default='')),
                ('Employee_regulatory_deductables_gross_percent', models.IntegerField()),
                ('regulatory_rates', models.IntegerField()),
                ('value', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('monthly_salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.employeesavedmonthlysalarystructure')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeSavedEmployeeReceivables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fixed_receivables_element', models.TextField(default='')),
                ('fixed_receivables_element_gross_percent', models.IntegerField()),
                ('value', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('monthly_salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.employeesavedmonthlysalarystructure')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeSavedEmployeeOtherDeductables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Employee_other_deductables', models.TextField(default='')),
                ('Employee_other_deductables_gross_percent', models.IntegerField()),
                ('value', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('monthly_salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.employeesavedmonthlysalarystructure')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeRegulatoryRecievables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Employee_regulatory_recievables', models.TextField(default='')),
                ('Employee_regulatory_recievables_gross_percent', models.IntegerField()),
                ('regulatory_rates', models.IntegerField()),
                ('value', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('monthly_salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.monthlysalarystructure')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeRegulatoryDeductables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Employee_regulatory_deductables', models.TextField(default='')),
                ('Employee_regulatory_deductables_gross_percent', models.IntegerField()),
                ('regulatory_rates', models.IntegerField()),
                ('value', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('monthly_salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.monthlysalarystructure')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeReceivables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fixed_receivables_element', models.TextField(default='')),
                ('fixed_receivables_element_gross_percent', models.IntegerField()),
                ('value', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('monthly_salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.monthlysalarystructure')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeOtherReceivables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('other_receivables_element', models.TextField(default='')),
                ('other_receivables_element_gross_percent', models.IntegerField()),
                ('value', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('monthly_salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.monthlysalarystructure')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeOtherDeductables',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Employee_other_deductables', models.TextField(default='')),
                ('Employee_other_deductables_gross_percent', models.IntegerField()),
                ('value', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('monthly_salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.monthlysalarystructure')),
            ],
        ),
    ]
