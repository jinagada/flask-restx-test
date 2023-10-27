import json
import logging
import os
import shutil

from flask import g
from flask_babel import gettext
from werkzeug.exceptions import NotFound

from ..configs import PROJECT_ID, PathConfig
from ..datasources import Sqlite3


class BoardService:
    """
    Board 데이터 처리
    """

    def __init__(self):
        """
        Class 생성 및 변수선언
        """
        self.logger = logging.getLogger(f'{PROJECT_ID}.services.BoardService')

    def _get_board_list(self, start_row, row_per_page, boards_code=None, board_seqs=None):
        """
        Board 목록 조회
        :param start_row:
        :type start_row:
        :param row_per_page:
        :type row_per_page:
        :param boards_code:
        :type boards_code:
        :param board_seqs:
        :type board_seqs:
        :return:
        :rtype:
        """
        select_sql = 'SELECT SEQ, BOARDS_CODE, TITLE, STRFTIME("%Y-%m-%dT%H:%M:%S", RDATE) AS RDATE, RUSER, STRFTIME("%Y-%m-%dT%H:%M:%S", MDATE) AS MDATE, MUSER FROM BOARDS'
        where_sql = ' WHERE 1 = 1'
        orderby_sql = ' ORDER BY RDATE DESC'
        limit_sql = ' LIMIT ?, ?'
        params = (start_row, row_per_page)
        # BoardsCode 조건 추가
        if boards_code:
            where_sql = where_sql + f' AND BOARDS_CODE = \'{boards_code}\''
        # board_seqs 조건 추가
        if board_seqs and len(board_seqs) > 0:
            where_sql = where_sql + f' AND SEQ IN ({",".join([str(u) for u in board_seqs])})'
            limit_sql = ''
            params = None
        sql = select_sql + where_sql + orderby_sql + limit_sql
        self.logger.debug(f'_get_user_list LIST sql : {sql}')
        board_list = Sqlite3().execute(sql, params)
        select_sql = 'SELECT COUNT(*) AS CNT FROM BOARDS'
        sql = select_sql + where_sql
        self.logger.debug(f'_get_user_list COUNT sql : {sql}')
        totalcount = Sqlite3().execute(query=sql, is_one=True)['CNT']
        return board_list, totalcount

    def get_board_list(self, start_row, row_per_page):
        """
        Board 페이징 목록 조회
        :param start_row:
        :type start_row:
        :param row_per_page:
        :type row_per_page:
        :return:
        :rtype:
        """
        return self._get_board_list(start_row, row_per_page)

    def get_board_list_by_boards_code(self, start_row, row_per_page, boards_code):
        """
        BoardsCode 조건의 Board 페이징 목록 조회
        :param start_row:
        :type start_row:
        :param row_per_page:
        :type row_per_page:
        :param boards_code:
        :type boards_code:
        :return:
        :rtype:
        """
        return self._get_board_list(start_row, row_per_page, boards_code)

    def get_board_list_by_board_seqs(self, board_seqs):
        """
        board_seqs 조건의 Board 페이징 목록 조회
        :param board_seqs:
        :type board_seqs:
        :return:
        :rtype:
        """
        return self._get_board_list(0, 0, board_seqs=board_seqs)

    @staticmethod
    def get_board_by_seq(board_seq):
        """
        Board 정보 조회
        :param board_seq:
        :return:
        """
        board_info = Sqlite3().execute('SELECT SEQ, BOARDS_CODE, TITLE, CONTENTS, ADD_FIELDS, STRFTIME("%Y-%m-%dT%H:%M:%S", RDATE) AS RDATE, RUSER, STRFTIME("%Y-%m-%dT%H:%M:%S", MDATE) AS MDATE, MUSER FROM BOARDS WHERE SEQ = ?', (board_seq,), True)
        board_info['ADD_FIELDS'] = json.loads(board_info['ADD_FIELDS'])
        return board_info

    @staticmethod
    def _insert_board(boards_code, title, contents, add_fields, user_id):
        """
        Board 정보 등록
        :param boards_code:
        :type boards_code:
        :param title:
        :type title:
        :param contents:
        :type contents:
        :param add_fields:
        :type add_fields:
        :param user_id:
        :type user_id:
        :return:
        :rtype:
        """
        result = Sqlite3().cmd('INSERT INTO BOARDS (BOARDS_CODE, TITLE, CONTENTS, ADD_FIELDS, RDATE, RUSER, MDATE, MUSER) VALUES (?, ?, ?, ?, DATETIME(\'now\', \'localtime\'), ?, DATETIME(\'now\', \'localtime\'), ?)',
                               (boards_code, title, contents, json.dumps(add_fields), user_id, user_id), True)
        return result

    @staticmethod
    def _update_board(board_seq, boards_code, title, contents, add_fields, user_id):
        """
        Board 정보 수정
        :param board_seq:
        :type board_seq:
        :param boards_code:
        :type boards_code:
        :param title:
        :type title:
        :param contents:
        :type contents:
        :param add_fields:
        :type add_fields:
        :param user_id:
        :type user_id:
        :return:
        :rtype:
        """
        result = Sqlite3().cmd('UPDATE BOARDS SET BOARDS_CODE = ?, TITLE = ?, CONTENTS = ?, ADD_FIELDS = ?, MUSER = ?, MDATE = DATETIME(\'now\', \'localtime\') WHERE SEQ = ?',
                               (boards_code, title, contents, json.dumps(add_fields), user_id, board_seq))
        return result

    def delete_boards(self, board_seq_list):
        """
        Board 삭제
        :param board_seq_list:
        :return:
        """
        # 파일 확인 후 삭제
        for board_seq in board_seq_list:
            self.save_board_file(int(board_seq), None, None, None, None, None)
        # 게시글 삭제
        in_query_str = ','.join(list(''.rjust(len(board_seq_list), '?')))
        result = Sqlite3().cmd(f'DELETE FROM BOARDS WHERE SEQ IN ({in_query_str})', tuple(board_seq_list))
        return result

    def save_board(self, board_seq, boards_code, title, contents, add_fields, user_id):
        """
        Board 정보 저장
        :param board_seq:
        :type board_seq:
        :param boards_code:
        :type boards_code:
        :param title:
        :type title:
        :param contents:
        :type contents:
        :param add_fields:
        :type add_fields:
        :param user_id:
        :type user_id:
        :return:
        :rtype:
        """
        if board_seq:
            board_info = self.get_board_by_seq(board_seq)
            if not board_info:
                raise NotFound(gettext(u'게시물이 존재하지 않습니다.'))
        else:
            board_info = None
        if board_info:
            result = self._update_board(board_seq, boards_code, title, contents, add_fields, user_id)
        else:
            result = self._insert_board(boards_code, title, contents, add_fields, user_id)
        if result < 1:
            raise SystemError('Save Board Error')
        return result

    @staticmethod
    def get_board_file_list(board_seq, is_key=False):
        """
        Board File 목록 조회
        :param board_seq:
        :param is_key:
        :return:
        """
        file_list = Sqlite3().execute('SELECT SEQ, BOARD_SEQ, PATH, FNAME, ONAME, STRFTIME("%Y-%m-%dT%H:%M:%S", RDATE) AS RDATE, RUSER FROM FILES WHERE BOARD_SEQ = ? ORDER BY SEQ', (board_seq,))
        if is_key:
            if file_list:
                file_info_list = {}
                for file in file_list:
                    file_info_list[file['SEQ']] = file
            else:
                file_info_list = None
        else:
            file_info_list = file_list
        return file_info_list

    @staticmethod
    def get_file_by_seq(file_seq):
        """
        File 정보 조회
        :param file_seq:
        :return:
        """
        file_info = Sqlite3().execute('SELECT SEQ, BOARD_SEQ, PATH, FNAME, ONAME, STRFTIME("%Y-%m-%dT%H:%M:%S", RDATE) AS RDATE, RUSER FROM FILES WHERE SEQ = ?', (file_seq,), True)
        return file_info

    @staticmethod
    def _insert_file(board_seq, path, fname, oname, user_id):
        """
        Board File 등록
        :param board_seq:
        :param path:
        :param fname:
        :param oname:
        :param user_id:
        :return:
        """
        result = Sqlite3().cmd('INSERT INTO FILES (BOARD_SEQ, PATH, FNAME, ONAME, RDATE, RUSER) VALUES (?, ?, ?, ?, DATETIME(\'now\', \'localtime\'), ?)',
                               (board_seq, path, fname, oname, user_id))
        return result

    @staticmethod
    def _update_file(file_seq, path, fname, oname, user_id):
        """
        Board File 변경
        :param file_seq:
        :param path:
        :param fname:
        :param oname:
        :param user_id:
        :return:
        """
        result = Sqlite3().cmd('UPDATE FILES SET PATH = ?, FNAME = ?, ONAME = ?, RUSER = ?, RDATE = DATETIME(\'now\', \'localtime\') WHERE SEQ = ?',
                               (path, fname, oname, user_id, file_seq))
        return result

    @staticmethod
    def _delete_file(file_seq):
        """
        첨부파일 정보 삭제
        :param file_seq:
        :return:
        """
        result = Sqlite3().cmd('DELETE FROM FILES WHERE SEQ = ?', (file_seq,))
        return result

    def save_board_file(self, board_seq, file_seqs, file_org_names, file_tmp_names, file_tmp_paths, user_id):
        """
        Board File 저장 처리
        :param board_seq:
        :param file_seqs:
        :param file_org_names:
        :param file_tmp_names:
        :param file_tmp_paths:
        :param user_id:
        :return:
        """
        # 업로드 디렉토리 설정
        upload_path = PathConfig[g.env_val]['file_path']
        file_base_path = PathConfig[g.env_val]['file_upload_home']
        os.makedirs(file_base_path + os.path.sep + upload_path, exist_ok=True)
        if file_seqs and len(file_seqs) > 0:
            # 등록된 데이터 조회
            file_seq_list = self.get_board_file_list(board_seq, True)
            for idx, file_seq in enumerate(file_seqs):
                # 등록된 데이터가 있는 경우
                if file_seq and file_seq_list:
                    # 기존 데이터와 비교 후 다르면 데이터 변경
                    old_info = file_seq_list[int(file_seq)]
                    if old_info and old_info['PATH'] != file_tmp_paths[idx]:
                        # 기존 파일 삭제
                        old_file_path = file_base_path + os.path.sep + old_info['PATH'] + os.path.sep + old_info['FNAME']
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                        # 임시파일을 실제 디렉토리로 이동
                        tmp_file_path = file_base_path + os.path.sep + file_tmp_paths[idx] + os.path.sep + file_tmp_names[idx]
                        new_file_path = file_base_path + os.path.sep + upload_path + os.path.sep + file_tmp_names[idx]
                        shutil.move(tmp_file_path, new_file_path)
                        # 변경된 파일로 다시 저장
                        self._update_file(file_seq, upload_path, file_tmp_names[idx], file_org_names[idx], user_id)
                # 등록된 데이터가 없는 경우
                elif not file_seq:
                    # 이동할 파일이 있는지 확인
                    if file_org_names[idx]:
                        # 임시파일을 실제 디렉토리로 이동
                        tmp_file_path = file_base_path + os.path.sep + file_tmp_paths[idx] + os.path.sep + file_tmp_names[idx]
                        new_file_path = file_base_path + os.path.sep + upload_path + os.path.sep + file_tmp_names[idx]
                        shutil.move(tmp_file_path, new_file_path)
                        # 파일등록
                        self._insert_file(board_seq, upload_path, file_tmp_names[idx], file_org_names[idx], user_id)
            # 삭제 대상 파일 확인 후 삭제
            if file_seq_list:
                for key in list(file_seq_list.keys()):
                    if str(key) not in file_seqs:
                        # 파일 삭제
                        old_info = file_seq_list[key]
                        old_file_path = file_base_path + os.path.sep + old_info['PATH'] + os.path.sep + old_info['FNAME']
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                        # 데이터 삭제
                        self._delete_file(key)
        else:  # 화면에서 등록한 파일이 없는경우 데이터를 확인 후 삭제
            # 등록된 데이터 조회
            file_seq_list = self.get_board_file_list(board_seq)
            for old_file in file_seq_list:
                # 파일 삭제
                old_file_path = file_base_path + os.path.sep + old_file['PATH'] + os.path.sep + old_file['FNAME']
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                # 데이터 삭제
                self._delete_file(old_file['SEQ'])
