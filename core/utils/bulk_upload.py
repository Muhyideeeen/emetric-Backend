def extract_key_message(errors: dict) -> tuple:
    """Returns key and message from dict of validation errors"""
    key = list(errors.keys())[0]
    message = errors[key]

    if isinstance(message, dict):
        key = list(message.keys())[0]
        message = message[key]
        if isinstance(message, dict):
            key = list(message.keys())[0]
            message = message[key]
        elif isinstance(message, list):
            message = message[0]

    elif isinstance(message, list):
        errors = message[0]
        if isinstance(message, dict):
            key = list(errors.keys())[0]
            message = errors[key][0]
        else:
            message = errors

    return str(key).replace('.', ' '), str(message)
