import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.template.defaultfilters import slugify

from client.models import Client

User = get_user_model()


class Structure(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    organisation_short_name = models.ForeignKey(
        Client,
        to_field="schema_name",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=128, unique=True, db_index=True)
    slug = models.SlugField(max_length=128, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower() if type(self.name) == str else self.name
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def parent_name(self):
        return self.organisation_short_name.schema_name

    class Meta:
        ordering = ["name"]
        abstract = True


class CorporateLevel(Structure):
    team_lead = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_lead_corporate_level",
    )


class Division(Structure):
    corporate_level = models.ForeignKey(
        CorporateLevel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="corporate_level_division",
    )
    team_lead = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_lead_division",
    )

    def parent_name(self):
        return self.corporate_level


class Group(Structure):
    division = models.ForeignKey(
        Division,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="division_group",
    )
    corporate_level = models.ForeignKey(
        CorporateLevel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="corporate_level_group",
    )
    team_lead = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_lead_group",
    )

    def parent_name(self):
        return self.division


class Department(Structure):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="group_department",
    )
    corporate_level = models.ForeignKey(
        CorporateLevel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="corporate_level_department",
    )
    team_lead = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_lead_department",
    )

    def parent_name(self):
        return self.group


class Unit(Structure):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="department_unit",
    )
    corporate_level = models.ForeignKey(
        CorporateLevel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="corporate_level_unit",
    )
    team_lead = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_lead_unit",
    )

    def parent_name(self):
        return self.department
