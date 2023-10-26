from enum import Enum

from flask_babel import gettext


class AuthCode(Enum):
    """
    로그인 가능한 사용자의 권한정보
    """
    ADMIN = gettext(u'관리자')
    USER = gettext(u'사용자')


class BoardsCode(Enum):
    NOTICE = gettext(u'공지사항')
    FAQ = gettext(u'FAQ')
    POST = gettext(u'게시물')
