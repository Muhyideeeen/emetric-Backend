# Generated by Django 3.2.13 on 2022-10-18 09:05

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CareerPath',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('career_path_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(blank=True, db_index=True, max_length=128, null=True, unique=True)),
                ('level', models.PositiveIntegerField(blank=True, db_index=True, null=True, unique=True)),
                ('educational_qualification', models.CharField(db_index=True, max_length=255)),
                ('years_of_experience_required', models.IntegerField(blank=True, db_index=True, null=True)),
                ('min_age', models.IntegerField(db_index=True)),
                ('max_age', models.IntegerField(db_index=True)),
                ('position_lifespan', models.IntegerField(db_index=True)),
                ('slots_available', models.IntegerField(db_index=True, default=1)),
                ('annual_package', models.IntegerField(db_index=True, default=1)),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]
