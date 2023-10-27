import typing as t

from flask_babel import gettext
from werkzeug.routing import BaseConverter, ValidationError

from ..enums import AuthCode, BoardsCode

# 오류 발생 시 공통 메시지
ERR_MSG = gettext(u'파라메터 Type 오류')


class IntListConverter(BaseConverter):
    """
    API route에서 path 파라메터에 숫자로된 배열을 사용할 수 있도록 Converter 추가
    예) <int_list:values>
    """
    regex = r'\d+(?:,\d+)*,?'

    def to_python(self, value: str) -> t.Any:
        try:
            return [int(x) for x in value.split(',')]
        except Exception:
            raise ValidationError(ERR_MSG)

    def to_url(self, value: t.Any) -> str:
        return ','.join(str(x) for x in value)


class AuthCodeConverter(BaseConverter):
    """
    API route에서 path 파라메터에 AuthCode Enum을 사용할 수 있도록 Converter 추가
    예) <auth_code:value>
    """
    def to_python(self, value: str) -> t.Any:
        try:
            request_type = [v for v in AuthCode if v.name == value]
            return request_type[0].name
        except Exception:
            raise ValidationError(ERR_MSG)

    def to_url(self, value: t.Any) -> str:
        return value


class BoardsCodeConverter(BaseConverter):
    """
    API route에서 path 파라메터에 BoardsCode Enum을 사용할 수 있도록 Converter 추가
    예) <boards_code:value>
    """
    def to_python(self, value: str) -> t.Any:
        try:
            request_type = [v for v in BoardsCode if v.name == value]
            return request_type[0].name
        except Exception:
            raise ValidationError(ERR_MSG)

    def to_url(self, value: t.Any) -> str:
        return value
