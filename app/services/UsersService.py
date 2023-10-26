import logging

from flask_babel import gettext
from werkzeug.exceptions import BadRequest, NotFound, Forbidden

from ..configs import PROJECT_ID
from ..datasources import Sqlite3
from ..enums import AuthCode


class UsersService:
    """
    Users 데이터 처리
    """

    def __init__(self):
        """
        Class 생성 및 변수선언
        """
        self.logger = logging.getLogger(f'{PROJECT_ID}.services.UsersService')

    @staticmethod
    def get_user_by_id(user_id):
        """
        User 정보 조회
        :param user_id:
        :return:
        """
        user_info = Sqlite3().execute('SELECT SEQ, USER_ID, USER_PW, USER_NAME, AUTH_CODE, STRFTIME("%Y-%m-%dT%H:%M:%S", RDATE) AS RDATE, STRFTIME("%Y-%m-%dT%H:%M:%S", MDATE) AS MDATE FROM USERS WHERE USER_ID = ?', (user_id,), True)
        return user_info

    @staticmethod
    def get_user_by_seq(user_seq):
        """
        User 정보 조회
        :param user_seq:
        :return:
        """
        user_info = Sqlite3().execute('SELECT SEQ, USER_ID, USER_PW, USER_NAME, AUTH_CODE, STRFTIME("%Y-%m-%dT%H:%M:%S", RDATE) AS RDATE, STRFTIME("%Y-%m-%dT%H:%M:%S", MDATE) AS MDATE FROM USERS WHERE SEQ = ?', (user_seq,), True)
        return user_info

    @staticmethod
    def _get_user_list(start_row, row_per_page, auth_code=None, user_seqs=None):
        """
        User 목록 조회
        :param start_row:
        :type start_row:
        :param row_per_page:
        :type row_per_page:
        :param auth_code:
        :type auth_code:
        :param user_seqs:
        :type user_seqs:
        :return:
        :rtype:
        """
        select_sql = 'SELECT SEQ, USER_ID, USER_PW, USER_NAME, AUTH_CODE, STRFTIME("%Y-%m-%dT%H:%M:%S", RDATE) AS RDATE, STRFTIME("%Y-%m-%dT%H:%M:%S", MDATE) AS MDATE FROM USERS '
        where_sql = ' WHERE 1 = 1'
        # 권한코드 조건 추가
        if auth_code:
            where_sql = where_sql + f' AND AUTH_CODE = \'{auth_code}\''
        # user_seqs 조건 추가
        if user_seqs and len(user_seqs) > 0:
            where_sql = where_sql + f' AND SEQ IN ({",".join([str(u) for u in user_seqs])})'
        orderby_sql = ' ORDER BY RDATE DESC LIMIT ?, ?'
        user_list = Sqlite3().execute(select_sql + where_sql + orderby_sql, (start_row, row_per_page))
        select_sql = 'SELECT COUNT(*) AS CNT FROM USERS'
        totalcount = Sqlite3().execute(query=select_sql + where_sql, is_one=True)['CNT']
        for user in user_list:
            user['RDATE'] = user['RDATE'] + '.000000+09:00'
            user['MDATE'] = user['MDATE'] + '.000000+09:00'
        return user_list, totalcount

    def get_user_list(self, start_row, row_per_page):
        """
        User 페이징 목록 조회
        :param start_row:
        :type start_row:
        :param row_per_page:
        :type row_per_page:
        :return:
        :rtype:
        """
        return self._get_user_list(start_row, row_per_page)

    def get_user_list_by_auth_code(self, start_row, row_per_page, auth_code):
        """
        AuthCode 조건의 User 페이징 목록 조회
        :param start_row:
        :type start_row:
        :param row_per_page:
        :type row_per_page:
        :param auth_code:
        :type auth_code:
        :return:
        :rtype:
        """
        return self._get_user_list(start_row, row_per_page, auth_code)

    def get_user_list_by_user_seqs(self, start_row, row_per_page, user_seqs):
        """
        user_seqs 조건의 User 페이징 목록 조회
        :param start_row:
        :type start_row:
        :param row_per_page:
        :type row_per_page:
        :param user_seqs:
        :type user_seqs:
        :return:
        :rtype:
        """
        return self._get_user_list(start_row, row_per_page, user_seqs=user_seqs)

    @staticmethod
    def _insert_user(user_id, user_pw, user_name, auth_code):
        """
        User 정보 등록
        :param user_id:
        :type user_id:
        :param user_pw:
        :type user_pw:
        :param user_name:
        :type user_name:
        :param auth_code:
        :type auth_code:
        :return:
        :rtype:
        """
        result = Sqlite3().cmd('INSERT INTO USERS (USER_ID, USER_PW, USER_NAME, AUTH_CODE, RDATE, MDATE) VALUES (?, ?, ?, ?, DATETIME(\'now\', \'localtime\'), DATETIME(\'now\', \'localtime\'))',
                               (user_id, user_pw, user_name, auth_code), True)
        return result

    @staticmethod
    def _update_mdate(user_id):
        """
        수정일 변경
        :return:
        """
        result = Sqlite3().cmd('UPDATE USERS SET MDATE = DATETIME(\'now\', \'localtime\') WHERE USER_ID = ?', (user_id,))
        return result

    def update_login_mdate(self, user_id):
        """
        로그인 처리 및 최종 로그인일 변경
        :param user_id:
        """
        if self.get_user_by_id(user_id):
            self._update_mdate(user_id)

    @staticmethod
    def _update_user(user_seq, user_id, user_pw, user_name):
        """
        User 정보 수정
        :param user_seq:
        :param user_id:
        :param user_pw:
        :param user_name:
        :return:
        """
        result = Sqlite3().cmd('UPDATE USERS SET USER_ID = ?, USER_PW = ?, USER_NAME = ?, MDATE = DATETIME(\'now\', \'localtime\') WHERE SEQ = ?',
                               (user_id, user_pw, user_name, user_seq))
        return result

    def save_user(self, user_id, user_pw, user_name, user_seq, auth_code):
        """
        User 정보 저장
        :param user_id:
        :type user_id:
        :param user_pw:
        :type user_pw:
        :param user_name:
        :type user_name:
        :param user_seq:
        :type user_seq:
        :param auth_code:
        :type auth_code:
        :return:
        :rtype:
        """
        if user_seq:
            user_info = self.get_user_by_seq(user_seq)
            if not user_info:
                raise NotFound(gettext(u'사용자가 존재하지 않습니다.'))
        else:
            user_info = None
        if user_info:
            if user_info['AUTH_CODE'] != auth_code:
                raise Forbidden(gettext(u'사용자의 권한정보는 변경 할 수 없습니다.'))
            result = self._update_user(user_seq, user_id, user_pw, user_name)
        else:
            result = self._insert_user(user_id, user_pw, user_name, auth_code)
        if result < 1:
            raise SystemError('Save User Error')
        return result

    @staticmethod
    def _delete_users(user_seq_list):
        """
        User 삭제
        :param user_seq_list:
        :return:
        """
        in_query_str = ','.join(list(''.rjust(len(user_seq_list), '?')))
        result = Sqlite3().cmd(f'DELETE FROM USERS WHERE SEQ IN ({in_query_str})', tuple(user_seq_list))
        return result

    def check_delete_users(self, user_seq_list):
        """
        확인 후 User 삭제
        :param user_seq_list:
        :return:
        """
        # 선택된 사용자에 관리자가 있는지 확인
        _, totalcount = self._get_user_list(0, 0, AuthCode.ADMIN.name, user_seq_list)
        if totalcount > 0:
            raise BadRequest(gettext(u'관리자는 삭제 할 수 없습니다.'))
        else:
            result = self._delete_users(user_seq_list)
        return result
