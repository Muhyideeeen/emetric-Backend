from import_export import resources, fields

from organization.models import CorporateLevel


class CorporateLevelResource(resources.ModelResource):
    """Resource to export CorporateLevel model"""

    name = fields.Field(attribute="name", column_name="name")
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
        model = CorporateLevel
        fields = ()
