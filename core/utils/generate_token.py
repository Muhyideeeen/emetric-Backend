from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def gen_token(user: User):
    token = RefreshToken.for_user(user)
    # Add custom claims
    token["email"] = user.email
    token["uuid"] = str(user.user_id)
    token["user_role"] = user.user_role.role

    return token


def update_login(refresh):
    data = dict()
    data["refresh"] = str(refresh)
    data["access"] = str(refresh.access_token)

    return data
