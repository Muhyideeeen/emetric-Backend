import uuid
from django.contrib.auth import get_user_model
from django.db import models

from cloudinary_storage.storage import RawMediaCloudinaryStorage

from tasks.models.detail import Task
from core.utils.validators import validate_file_extension_for_pdf


BASE_FILE_PATH = "tasks_submission/"
User = get_user_model()


class TaskSubmission(models.Model):
    task_submission_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    user = models.ForeignKey(
        User,
        db_index=True,
        to_field="user_id",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="submission_user",
    )
    task = models.ForeignKey( 
        Task, on_delete=models.CASCADE, related_name="task_submission"
    )
    submission = models.FileField(
        upload_to=(BASE_FILE_PATH),
        db_index=True,
        null=True,
        validators=[validate_file_extension_for_pdf],
        storage=RawMediaCloudinaryStorage(),
    )
    quantity_target_unit_achieved = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
