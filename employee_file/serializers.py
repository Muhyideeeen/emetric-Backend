from rest_framework import serializers

from employee.models import Employee
from employee_file.models import EmployeeFile, EmployeeFileName


class EmployeeFileNameSerializer(serializers.ModelSerializer):
    """Serializer for EmployeeFileName"""

    class Meta:
        model = EmployeeFileName
        fields = "__all__"

    def create(self, validated_data):
        return super().create(validated_data)


class EmployeeFileSerializer(serializers.ModelSerializer, ):
    """Serializer for EmployeeFile"""

    employee = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Employee.objects.all(), write_only=True
    )

    class Meta:
        model = EmployeeFile
        exclude = ["id"]
        lookup_field = "uuid"

    def create(self, validated_data):
        validated_data = self._process_serialized_input(validated_data)
        return super().create(validated_data)

    def _process_serialized_input(self, validated_data):
        name = validated_data.get("name")
        employee_files = EmployeeFile.objects.filter(name=name).order_by(
            "-created_at"
        )
        if employee_files.exists():
            validated_data.update({"value": employee_files.first().value + 1})

        return validated_data
