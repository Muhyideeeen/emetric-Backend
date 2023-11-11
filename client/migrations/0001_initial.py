# Generated by Django 3.2.13 on 2022-10-18 09:06

import cloudinary_storage.storage
import core.utils.base_upload
from django.db import migrations, models
import django.db.models.deletion
import django_tenants.postgresql_backend.base
import multiselectfield.db.fields
import timezone_field.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('schema_name', models.CharField(db_index=True, max_length=63, unique=True, validators=[django_tenants.postgresql_backend.base._check_schema_name])),
                ('timezone', timezone_field.fields.TimeZoneField(default='UTC')),
                ('company_name', models.CharField(max_length=255)),
                ('company_logo', models.ImageField(blank=True, null=True, storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(), upload_to=core.utils.base_upload.Upload('company_logo/'))),
                ('owner_email', models.EmailField(db_index=True, max_length=255)),
                ('owner_first_name', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('owner_last_name', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('owner_phone_number', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('work_start_time', models.TimeField()),
                ('work_stop_time', models.TimeField()),
                ('work_break_start_time', models.TimeField()),
                ('work_break_stop_time', models.TimeField()),
                ('work_days', multiselectfield.db.fields.MultiSelectField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], default='0,1,2,3,4', max_length=13)),
                ('employee_limit', models.PositiveIntegerField(default=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(db_index=True, max_length=253, unique=True)),
                ('is_primary', models.BooleanField(db_index=True, default=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='domains', to='client.client')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
