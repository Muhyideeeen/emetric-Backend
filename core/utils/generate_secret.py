import secrets


def generate_secret(length: int):
    return secrets.token_urlsafe(length)


print(generate_secret(64))
