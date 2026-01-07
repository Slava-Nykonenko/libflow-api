from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils.translation import gettext as _

from user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "is_staff",
        )
        read_only_fields = (
            "id",
            "is_staff",
        )
        extra_kwargs = {
            "password": {
                "write_only": True,
                "min_length": 8,
                "style": {"input_type": "password"},
                "label": _("Password"),
            },
        }

    def create(self, validated_data: dict[str, Any]) -> User:
        """Create User with encrypted password"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        """Update User with encrypted password"""
        password = validated_data.get("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class UserListSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ("id", "first_name", "last_name")
