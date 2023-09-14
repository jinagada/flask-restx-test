import logging

from werkzeug.exceptions import BadRequest, NotFound

from ..configs import PROJECT_ID
from ..datasources import Sqlite3


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
        user_info = Sqlite3().execute('SELECT SEQ, USER_ID, USER_PW, USER_NAME, STRFTIME("%Y-%m-%dT%H:%M:%S", RDATE) AS RDATE, STRFTIME("%Y-%m-%dT%H:%M:%S", MDATE) AS MDATE FROM USERS WHERE USER_ID = ?', (user_id,), True)
        return user_info

    @staticmethod
    def get_user_by_seq(user_seq):
        """
        User 정보 조회
        :param user_seq:
        :return:
        """
        user_info = Sqlite3().execute('SELECT SEQ, USER_ID, USER_PW, USER_NAME, STRFTIME("%Y-%m-%dT%H:%M:%S", RDATE) AS RDATE, STRFTIME("%Y-%m-%dT%H:%M:%S", MDATE) AS MDATE FROM USERS WHERE SEQ = ?', (user_seq,), True)
        return user_info

    @staticmethod
    def get_user_list(start_row, row_per_page):
        """
        User 목록 조회
        :param start_row:
        :param row_per_page:
        :return:
        """
        user_list = Sqlite3().execute('SELECT SEQ, USER_ID, USER_PW, USER_NAME, STRFTIME("%Y-%m-%dT%H:%M:%S", RDATE) AS RDATE, STRFTIME("%Y-%m-%dT%H:%M:%S", MDATE) AS MDATE FROM USERS ORDER BY RDATE DESC LIMIT ?, ?', (start_row, row_per_page))
        totalcount = Sqlite3().execute(query='SELECT COUNT(*) AS CNT FROM USERS', is_one=True)['CNT']
        return user_list, totalcount

    @staticmethod
    def _insert_user(user_id, user_pw, user_name):
        """
        User 정보 등록
        :param user_id:
        :param user_pw:
        :param user_name:
        :return:
        """
        result = Sqlite3().cmd('INSERT INTO USERS (USER_ID, USER_PW, USER_NAME, RDATE, MDATE) VALUES (?, ?, ?, DATETIME(\'now\', \'localtime\'), DATETIME(\'now\', \'localtime\'))',
                               (user_id, user_pw, user_name), True)
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

    def save_user(self, user_id, user_pw, user_name, user_seq):
        """
        User 정보 저장
        :param user_id:
        :param user_pw:
        :param user_name:
        :param user_seq:
        :return:
        """
        if user_seq:
            user_info = self.get_user_by_seq(user_seq)
            if not user_info:
                raise NotFound('사용자가 존재하지 않습니다.')
        else:
            user_info = None
        if user_info:
            result = self._update_user(user_seq, user_id, user_pw, user_name)
        else:
            result = self._insert_user(user_id, user_pw, user_name)
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
        _, totalcount = self.get_user_list(0, 10)
        if totalcount < 2 or totalcount == len(user_seq_list):
            raise BadRequest('사용자를 전부 삭제 할 수 없습니다.')
        else:
            result = self._delete_users(user_seq_list)
        return result
