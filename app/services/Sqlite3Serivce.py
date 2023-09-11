import logging

from ..configs import PROJECT_ID
from ..datasources import Sqlite3


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
        self._make_table_boards()
        self._make_table_files()

    def _make_table_boards(self):
        """
        테이블 생성
        :return:
        """
        Sqlite3().cmd(query='''CREATE TABLE IF NOT EXISTS BOARDS
        (SEQ INTEGER PRIMARY KEY AUTOINCREMENT,
         TITLE TEXT,
         CONTENTS TEXT,
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
