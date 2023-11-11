import sys
from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from redis import AuthenticationError


def compressImage(uploadedImage, width=200, height=200):
    """
    Returns a compressed version of an image
    """
    # Transpose image because of temporary storage
    imageTemporary = ImageOps.exif_transpose(Image.open(uploadedImage))
    outputIoStream = BytesIO()
    imageTemporaryResized = imageTemporary.resize((width, height))

    if imageTemporaryResized.mode == "JPEG":
        imageTemporaryResized.save(outputIoStream, format="JPEG", quality=100)

    elif imageTemporaryResized.mode in ["RGBA", "P", "RGB"]:
        imageTemporaryResized = imageTemporaryResized.convert("RGB")
        imageTemporaryResized.save(outputIoStream, format="JPEG", quality=100)
    outputIoStream.seek(0)
    uploadedImage = InMemoryUploadedFile(
        outputIoStream,
        "ImageField",
        "%s.jpg" % uploadedImage.name.split(".")[0],
        "image/jpeg",
        sys.getsizeof(outputIoStream),
        None,
    )
    return uploadedImage
