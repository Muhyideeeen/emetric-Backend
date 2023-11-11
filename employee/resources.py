from import_export import resources, fields

from employee.models import Employee


class EmployeeResource(resources.ModelResource):
    """Resource to export Employee model"""

    first_name = fields.Field(
        attribute="user__first_name", column_name="first_name"
    )
    last_name = fields.Field(
        attribute="user__last_name", column_name="last_name"
    )
    phone_number = fields.Field(
        attribute="user__phone_number", column_name="phone_number"
    )
    official_email = fields.Field(
        attribute="user__email", column_name="official_email"
    )
    personal_phone = fields.Field(
        attribute="employee_contact_infomation__phone_number",
        column_name="personal_phone",
    )
    personal_email = fields.Field(
        attribute="employee_contact_infomation__personal_email",
        column_name="personal_email",
    )
    address = fields.Field(
        attribute="employee_contact_infomation__address", column_name="address"
    )
    date_of_birth = fields.Field(
        attribute="employee_basic_infomation__date_of_birth",
        column_name="date_of_birth",
    )
    education_details_institutions = fields.Field()
    education_details_years = fields.Field()
    education_details_qualifications = fields.Field()
    guarantor_1_first_name = fields.Field(
        attribute="employee_contact_infomation__guarantor_one_first_name",
        column_name="guarantor_1_first_name",
    )
    guarantor_1_last_name = fields.Field(
        attribute="employee_contact_infomation__guarantor_one_last_name",
        column_name="guarantor_1_last_name",
    )
    guarantor_1_address = fields.Field(
        attribute="employee_contact_infomation__guarantor_one_address",
        column_name="guarantor_1_address",
    )
    guarantor_1_occupation = fields.Field(
        attribute="employee_contact_infomation__guarantor_one_occupation",
        column_name="guarantor_1_occupation",
    )
    guarantor_1_age = fields.Field(
        attribute="employee_contact_infomation__guarantor_one_age",
        column_name="guarantor_1_age",
    )
    guarantor_2_first_name = fields.Field(
        attribute="employee_contact_infomation__guarantor_two_first_name",
        column_name="guarantor_2_first_name",
    )
    guarantor_2_last_name = fields.Field(
        attribute="employee_contact_infomation__guarantor_two_last_name",
        column_name="guarantor_2_last_name",
    )
    guarantor_2_address = fields.Field(
        attribute="employee_contact_infomation__guarantor_two_address",
        column_name="guarantor_2_address",
    )
    guarantor_2_occupation = fields.Field(
        attribute="employee_contact_infomation__guarantor_two_occupation",
        column_name="guarantor_2_occupation",
    )
    guarantor_2_age = fields.Field(
        attribute="employee_contact_infomation__guarantor_two_age",
        column_name="guarantor_2_age",
    )
    description = fields.Field(
        attribute="employee_basic_infomation__brief_description",
        column_name="description",
    )
    role = fields.Field(attribute="user__user_role", column_name="role")
    date_employed = fields.Field(
        attribute="employee_employmentinformation__date_employed",
        column_name="date_employed",
    )
    corporate_name = fields.Field(
        attribute="corporate_level__name", column_name="corporate_name"
    )
    division_name = fields.Field(
        attribute="division__name", column_name="division_name"
    )
    group_name = fields.Field(
        attribute="group__name", column_name="group_name"
    )
    department_name = fields.Field(
        attribute="department__name", column_name="department_name"
    )
    unit_name = fields.Field(attribute="unit__name", column_name="unit_name")
    career_level = fields.Field(
        attribute="career_path__level", column_name="career_level"
    )
    designation_name = fields.Field(
        attribute="employee_basic_infomation__designation__name",
        column_name="designation_name",
    )
    employment_status = fields.Field(
        attribute="employee_employmentinformation__status",
        column_name="employment_status",
    )

    class Meta:
        model = Employee
        fields = ()

    def dehydrate_education_details_institutions(self, obj):
        return ", ".join(
            list(
                obj.employee_basic_infomation.education_details.all().values_list(
                    "institution", flat=True
                )
            )
        )

    def dehydrate_education_details_years(self, obj):
        years_int_list = list(
            obj.employee_basic_infomation.education_details.all().values_list(
                "year", flat=True
            )
        )
        years_str_list = [str(year) for year in years_int_list]
        return ", ".join(years_str_list)

    def dehydrate_education_details_qualifications(self, obj):
        return ", ".join(
            list(
                obj.employee_basic_infomation.education_details.all().values_list(
                    "qualification", flat=True
                )
            )
        )
