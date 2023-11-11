import uuid


def modify_filename(filename: str) -> str:
    ext = filename.split(".")[-1]
    return f"{uuid.uuid4()}.{ext}"
