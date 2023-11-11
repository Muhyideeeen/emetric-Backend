from rest_framework import serializers

from account.models import Role


class RoleSerializer(serializers.ModelSerializer):
    role = serializers.CharField(required=True)

    class Meta:
        model = Role
        fields = ["role"]
