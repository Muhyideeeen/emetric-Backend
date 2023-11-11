import os
import time

from django.utils.deconstruct import deconstructible

from core.utils.modify_filename import modify_filename


@deconstructible
class Upload:
    def __init__(self, base_upload_path):
        self.base_upload_path = base_upload_path

    def __call__(self, instance, filename):
        new_filename = modify_filename(filename=filename)
        return os.path.join(
            f'{self.base_upload_path}/{time.strftime("%Y/%m/%d/")}',
            new_filename,
        )
