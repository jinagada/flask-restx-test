import logging
import sqlite3

from ..configs import PROJECT_ID


def _dict_factory(cursor, row):
    """
    tuple -> dict
    :param cursor:
    :param row:
    :return:
    """
    new_row = {}
    for idx, col in enumerate(cursor.description):
        new_row[col[0]] = row[idx]
    return new_row


class Sqlite3:
    """
    Sqlite3 연동 Class
    """

    def __init__(self):
        """
        Class 생성 및 변수선언
        """
        self.logger = logging.getLogger(f'{PROJECT_ID}.datasources.Sqlite3')
        self.db_conn = None

    def __del__(self):
        """
        Class 삭제
        """
        self._close_conn()

    def _get_conn(self):
        """
        Connection 연결
        """
        try:
            if self.db_conn is None:
                self.db_conn = sqlite3.connect('sample.db')
                self.db_conn.row_factory = _dict_factory
        except Exception as e:
            raise SystemError(e)

    def _close_conn(self):
        """
        Connection 닫기
        """
        try:
            if self.db_conn is not None:
                self.db_conn.close()
                self.db_conn = None
        except Exception as e:
            raise SystemError(e)

    def execute(self, query, params=None, is_one=False):
        """
        SELECT 실행 및 결과반환
        :param query:
        :param params:
        :param is_one:
        :return:
        """
        try:
            self._get_conn()
            cur = self.db_conn.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            if is_one:
                result = cur.fetchone()
            else:
                result = cur.fetchall()
            cur.close()
        except Exception as e:
            raise SystemError(e)
        finally:
            self._close_conn()
        return result

    def cmd(self, query, params=None, is_lastrowid=False):
        """
        INSERT, UPDATE, DELETE, CREATE 실행 및 결과반환
        :param query:
        :param params:
        :param is_lastrowid:
        :return:
        """
        try:
            self._get_conn()
            if params:
                cursor = self.db_conn.execute(query, params)
            else:
                cursor = self.db_conn.execute(query)
            self.db_conn.commit()
            if is_lastrowid:
                result = cursor.lastrowid
            else:
                result = cursor.rowcount
        except Exception as e:
            raise SystemError(e)
        finally:
            self._close_conn()
        return result
