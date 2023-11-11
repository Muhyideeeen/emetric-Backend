from django.contrib.auth import get_user_model
from django.db import models

from tracking.models.base_tracking_model import TrackingBaseModel

User = get_user_model()


class PasswordUpdateTrackingManager(models.Manager):

    def create_password_update_tracking(self, **kwargs):
        return self.create(**kwargs)


class PasswordUpdateTracking(TrackingBaseModel):

    is_password_updated: bool = models.BooleanField(default=True)

    objects = PasswordUpdateTrackingManager()
