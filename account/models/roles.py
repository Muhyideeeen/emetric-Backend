from django.db import models


class Role(models.Model):
    """
    The Role entries are managed by the system,
    automatically created via a Django data migration.
    """

    EMPLOYEE = 'employee'
    TEAM_LEAD = 'team_lead'
    ADMIN = 'admin'
    ADMIN_HR = 'admin_hr'
    SUPER_ADMIN = 'super_admin'
    Exco_or_Management = 'Exco_or_Management'
    Committee_Member = 'Committee_Member'
    Committee_Chair = 'Committee_Chair'


    ROLE_CHOICES = (
        (EMPLOYEE, 'Employee'),
        (TEAM_LEAD, 'Team Lead'),
        (ADMIN, 'Admin'),
        (ADMIN_HR, 'Admin HR'),
        (SUPER_ADMIN, 'Super Admin'),

        (Exco_or_Management,'Exco/Management'),
        (Committee_Member,  'Committee Member'),
        (Committee_Chair, 'Committee Chair'),

    )

    role = models.CharField(max_length=25, choices=ROLE_CHOICES)

    objects = models.Manager()

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.role
