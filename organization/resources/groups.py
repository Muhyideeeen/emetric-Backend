from __future__ import division
from import_export import resources, fields

from organization.models import Group


class GroupResource(resources.ModelResource):
    """Resource to export Group model"""

    name = fields.Field(attribute="name", column_name="name")
    corporate_level = fields.Field(
        attribute="corporate_level__name", column_name="corporate_level"
    )
    division = fields.Field(attribute="division__name", column_name="division")
    team_lead_first_name = fields.Field(
        attribute="team_lead__first_name", column_name="team_lead_first_name"
    )
    team_lead_last_name = fields.Field(
        attribute="team_lead__last_name", column_name="team_lead_last_name"
    )
    team_lead_email = fields.Field(
        attribute="team_lead__email", column_name="team_lead_email"
    )

    class Meta:
        model = Group
        fields = ()
