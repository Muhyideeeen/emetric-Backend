def get_client_ip(request):
    """
    Get User IP address
    Args:
        request:

    Returns:

    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        _ip = x_forwarded_for.split(",")[0]
    else:
        _ip = request.META.get("REMOTE_ADDR")
    return _ip
