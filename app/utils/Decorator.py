from functools import wraps

from flask_babel import gettext
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from werkzeug.exceptions import Forbidden

from ..enums import AuthCode


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
            # flask_jwt_extended.verify_jwt_in_request() can be used to build your own decorators. This is the same function used by flask_jwt_extended.jwt_required().
            verify_jwt_in_request()
            claims = get_jwt()
            if claims['aud'] == AuthCode.ADMIN.name:
                return fn(*args, **kwargs)
            else:
                # gettext에서 문자열 내부 변수 사용시 한글과 충돌이 발생하여 변수 사용없이 메시지를 처리함
                # raise Forbidden(gettext(u'%(auth_code) 권한이 필요합니다.', auth_code=AuthCode.ADMIN.value)) : ValueError: unsupported format character '?' (0xad8c) at index 8
                raise Forbidden(gettext(u'관리자 권한이 필요합니다.'))
        return decorator
    return wrapper
