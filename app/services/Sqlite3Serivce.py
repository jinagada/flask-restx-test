import logging

import bcrypt

from ..configs import PROJECT_ID
from ..datasources import Sqlite3
from ..enums import AuthCode


class Sqlite3Service:
    """
    Sqlite3 Database 초기 데이터 설정
    """

    def __init__(self):
        """
        Class 생성
        """
        self.logger = logging.getLogger(f'{PROJECT_ID}.services.Sqlite3Service')
        # 테이블 생성
        self._make_table_users()
        self._make_table_boards()
        self._make_table_files()
        # 최초 사용자 등록
        if self._check_table_users() < 1:
            self._insert_first_user()

    def _check_table_users(self):
        """
        테이블 확인
        :return:
        """
        tmp = Sqlite3().execute(query='SELECT COUNT(*) AS CNT FROM USERS')
        result = tmp[0]['CNT']
        self.logger.info(f'Check USERS Table : {result}')
        return result

    def _insert_first_user(self):
        """
        최초 사용자 등록
        :return:
        """
        # 비밀번호 암호화(Bcrypt) : Java Spring 기본값을 사용하여 호환성 유지
        password_bcrypt = bcrypt.hashpw('1234!'.encode('utf-8'), bcrypt.gensalt(10, b'2a'))
        result = Sqlite3().cmd('INSERT INTO USERS (USER_ID, USER_PW, USER_NAME, AUTH_CODE, RDATE, MDATE) VALUES (?, ?, ?, ?, DATETIME(\'now\', \'localtime\'), DATETIME(\'now\', \'localtime\'))',
                               ('admin', password_bcrypt, 'Admin User', AuthCode.ADMIN.name), True)
        self.logger.info(f'Insert USER : {result}')
        return result

    def _make_table_users(self):
        """
        테이블 생성
        :return:
        """
        Sqlite3().cmd(query='''CREATE TABLE IF NOT EXISTS USERS
        (SEQ INTEGER PRIMARY KEY AUTOINCREMENT,
         USER_ID TEXT UNIQUE,
         USER_PW TEXT,
         USER_NAME TEXT,
         AUTH_CODE TEXT,
         RDATE TEXT,
         MDATE TEXT)''')
        self.logger.info('Maked USERS Table')

    def _make_table_boards(self):
        """
        테이블 생성
        JSON column type을 사용하기 위해서는 3.40.x 이상이 필요 해 보임
        테스트된 버전은 3.43.2 버전임 : sqlite3 --version
        :return:
        """
        Sqlite3().cmd(query='''CREATE TABLE IF NOT EXISTS BOARDS
        (SEQ INTEGER PRIMARY KEY AUTOINCREMENT,
         BOARDS_CODE TEXT,
         TITLE TEXT,
         CONTENTS TEXT,
         ADD_FIELDS JSON,
         RDATE TEXT,
         RUSER TEXT,
         MDATE TEXT,
         MUSER TEXT)''')
        self.logger.info('Maked BOARDS Table')

    def _make_table_files(self):
        """
        테이블 생성
        :return:
        """
        Sqlite3().cmd(query='''CREATE TABLE IF NOT EXISTS FILES
        (SEQ INTEGER PRIMARY KEY AUTOINCREMENT,
         BOARD_SEQ INTEGER,
         PATH TEXT,
         FNAME TEXT,
         ONAME TEXT,
         RDATE TEXT,
         RUSER TEXT)''')
        self.logger.info('Maked FILES Table')
