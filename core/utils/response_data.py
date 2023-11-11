"""
Response data module
"""
from typing import Dict, Union, List


def response_data(
    status: int, message: str, data: Union[None, Dict, List] = None
) -> Dict:
    """
    data response function
    :param status
    :param message:
    :param data:
    :return:
    """
    payload = {
        "status": status,
        "message": message,
    }
    if data is not None:
        payload.update(
            {"error": data}
        ) if 400 <= status <= 600 else payload.update({"data": data})
    return payload
