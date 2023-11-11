from django.contrib.auth import get_user_model
from django.db import connection

from account.models.email_invitation import EmailInvitation
from client.models import Domain
from core.utils.modify_raw_sql import dictfetchall


User = get_user_model()


def delete_client(client) -> None:
    """Deletes a tenant schema, client account and all associated
    user rows


    Args:
        client ([type]): [description]
    """
    user = User.objects.get(email=client.owner_email)

    Domain.objects.filter(tenant_id=client.id).delete()
    EmailInvitation.objects.filter(user__email=user.email).delete()

    token = None
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM token_blacklist_outstandingtoken WHERE user_id=%s",
            [user.id],
        )
        tokens = dictfetchall(cursor)

        for token in tokens:
            cursor.execute(
                "DELETE FROM token_blacklist_blacklistedtoken WHERE token_id=%s",
                [token["id"]],
            )

    with connection.cursor() as cursor:

        cursor.execute(
            "DELETE FROM token_blacklist_outstandingtoken WHERE user_id=%s",
            [user.id],
        )

    with connection.cursor() as cursor:

        cursor.execute(
            "DELETE FROM django_tenants_celery_beat_periodictasktenantlink WHERE tenant_id=%s",
            [client.id],
        )

    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM django_celery_beat_periodictask WHERE headers=%s",
            [f'{{"_schema_name": "{client.schema_name}"}}'],
        )

    connection.set_schema(schema_name=client.schema_name)
    client.delete()

    with connection.cursor() as cursor:
        cursor.execute(f"DROP SCHEMA {client.schema_name} CASCADE;")

    connection.set_schema(schema_name="public")

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM account_user WHERE id=%s", [user.id])
