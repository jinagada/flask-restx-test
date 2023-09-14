from functools import wraps

from flask_jwt_extended import verify_jwt_in_request, get_jwt
from werkzeug.exceptions import Forbidden


def admin_required():
    """
    # Here is a custom decorator that verifies the JWT is present in the request,
    # as well as insuring that the JWT has a claim indicating that this user is
    # an administrator

    ADMIN 권한 확인용 decorator
    :return:
    :rtype:
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims['aud'] == 'ADMIN':
                return fn(*args, **kwargs)
            else:
                raise Forbidden('ADMIN 권한이 필요합니다.')
        return decorator
    return wrapper
