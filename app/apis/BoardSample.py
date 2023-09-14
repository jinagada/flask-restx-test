import logging
import os
import uuid
from http import HTTPStatus

from flask import g
from flask_jwt_extended import jwt_required, current_user, get_jwt_identity
from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import NotFound

import app
from ..configs import PathConfig, PROJECT_ID
from ..services import BoardService

# path에 설정된 URL을 기준으로 각 Namespace가 구분됨
# path에 설정된값은 Namespace가 가지는 URL prefix로 설정됨
board_sample = Namespace(
    path='/board',
    name='Board Sample',
    description='간단한 게시판 예제'
)
# Namespace logger 설정
board_sample.logger = logging.getLogger(f'{PROJECT_ID}.apis.BoardSample')


class _Schema:
    """
    게시물에서 사용하는 파라메터 및 모델 정의
    모델이 Namespace에 등록되는 구조로 되어있어 별도의 디렉토리로 분리하기 어려움
    """
    # 게시물 목록 조회 query 파라메터
    # type=int 인 경우 파라메터에 값이 없으면, default 값이 있어도 parse_args 실행시 설정이 되지 않음
    board_list_params = reqparse.RequestParser()
    board_list_params.add_argument('start_row', location='args', type=int, required=True, default=0, help='시작행 번호')
    board_list_params.add_argument('row_per_page', location='args', type=int, required=True, default=10, help='화면당 행 수')
    # 게시물 상세 모델
    board_save_model = board_sample.model('BoardSave', {
        'title': fields.String(description='게시물 제목', example='제목', attribute='TITLE', required=True, min_length=1, max_length=200),
        'contents': fields.String(description='게시물 내용', example='내용', attribute='CONTENTS', required=True, min_length=1)
    })
    board_detail_model = board_sample.inherit('BoardDetail', board_save_model, {
        'board_seq': fields.Integer(description='게시물 번호', example=1, attribute='SEQ'),
        'r_user_id': fields.String(description='작성자', example='UserId', attribute='RUSER'),
        'm_user_id': fields.String(description='수정자', example='UserId', attribute='MUSER'),
        'rdate': fields.DateTime(description='등록일시', example='2023-09-06T14:42:06', attribute='RDATE'),
        'mdate': fields.DateTime(description='수정일시', example='2023-09-06T14:42:06', attribute='MDATE')
    })
    # 게시물 등록 결과
    board_save_result_model = board_sample.model('BoardSaveResult', {
        'result': fields.String(description='결과', example='Success'),
        'board_seq': fields.Integer(description='게시물 번호', example=1)
    })
    # 게시물 삭제 결과
    board_delete_result_model = board_sample.model('BoardDeleteResult', {
        'result': fields.String(description='결과', example='Success'),
        'deleted_count': fields.Integer(description='삭제된 게시물수', example=1)
    })
    # 게시물 목록 모델
    board_list_model = board_sample.model('BoardListResult', {
        'totalcount': fields.Integer(description='게시물 전체수', example=100),
        # 게시물 상세 모델을 목록에 사용, skip_none 옵션으로 값이 없는 필드 제거
        'board_list': fields.List(fields.Nested(board_detail_model, skip_none=True))
    })
    # 파일 업로드 파라메터
    # 아직은 다른 type의 파라메터를 추가하거나 여러 파일 동시 업로드는 지원하지 않아보임
    # 한번에 하나의 파일만 업로드 가능함
    file_upload_params = board_sample.parser()
    file_upload_params.add_argument('file', location='files', type=FileStorage, required=True, help='업로드 파일')
    # 파일 업로드 결과 모델
    file_upload_result_model = board_sample.model('FileUploadResult', {
        'result': fields.String(description='결과', example='Success'),
        'file_org_name': fields.String(description='원본 파일명', example='aaa.txt'),
        'file_tmp_path': fields.String(description='파일의 임시 디렉토리', example='tmp'),
        'file_tmp_name': fields.String(description='파일의 임시 파일명', example='beb7728bebcb430c9c63716caed6b808.txt')
    })
    # 업로드된 파일정보 저장 모델
    file_save_model = board_sample.model('FileSave', {
        # fields 로 선언되는 모든 타입은 None을 하용하지 않음
        'file_seq': fields.String(description='파일 일련번호', example='번호가 있는 경우 양수(1,2,3), 없는 경우는 공백문자("")'),
        'file_org_name': fields.String(description='원본 파일명', example='aaa.txt', required=True, min_length=1, max_length=255),
        'file_tmp_name': fields.String(description='파일의 임시 파일명', example='beb7728bebcb430c9c63716caed6b808.txt', required=True, min_length=1, max_length=255),
        'file_tmp_path': fields.String(description='파일의 임시 디렉토리', example='tmp', required=True, min_length=1, max_length=255)
    })
    # 파일정보 상세
    file_detail_model = board_sample.model('FileDetail', {
        'file_seq': fields.Integer(description='파일 일련번호', example=1, attribute='SEQ'),
        'board_seq': fields.Integer(description='게시물 번호', example=1, attribute='BOARD_SEQ'),
        'file_path': fields.String(description='파일 경로', example='upload', attribute='PATH'),
        'file_name': fields.String(description='파일명', example='beb7728bebcb430c9c63716caed6b808.txt', attribute='FNAME'),
        'file_org_name': fields.String(description='원본 파일명', example='aaa.txt', attribute='ONAME'),
        'rdate': fields.DateTime(description='등록일시', example='2023-09-06T14:42:06', attribute='RDATE'),
        'r_user_id': fields.String(description='작성자', example='UserId', attribute='RUSER')
    })
    # 실제 파라메터로 넘길 파일정보 목록 모델
    file_save_list_model = board_sample.model('FileSaveList', {
        'file_list': fields.List(fields.Nested(file_save_model))
    })
    # 파일 목록 모델
    file_list_model = board_sample.model('FileList', {
        'board_seq': fields.Integer(description='게시물 번호', example=1),
        'file_list': fields.List(fields.Nested(file_detail_model, skip_none=True))
    })
    # 파일정보 저장 결과 모델
    file_save_result_model = board_sample.inherit('FileSaveResult', file_list_model, {
        'result': fields.String(description='결과', example='Success')
    })


# Namespace에 설정된 path값 이후의 URL을 route에 추가할 수 있음
@board_sample.route('')
# 모든 METHOD에 동일한 code가 사용되는 경우 class에 설정하면 한번에 적용 가능함
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.system_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.system_error_model)
class BoardPost(Resource):
    """
    게시물 목록 조회, 게시물 등록
    """
    # request : query 파라메터에서도 validate 옵션을 사용하면 설정된 유효성 검사가 function 진입전에 실행됨
    @jwt_required(optional=True)
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.system_error_model)
    @board_sample.expect(_Schema.board_list_params, validate=True)
    # response : marshal_with를 사용하면 결과값에 대한 모델매핑과 apidoc을 한번에 작성 할 수 있음
    @board_sample.marshal_with(_Schema.board_list_model, code=int(HTTPStatus.OK), description='게시물 목록')
    def get(self):
        """
        게시물 목록 조회
        :return:
        :rtype:
        """
        # JWT TOKEN 이 있는경우 해당 정보를 로그로 남김
        current_identity = get_jwt_identity()
        if current_identity:
            # Namespace logger 사용
            board_sample.logger.info(f'게시물 조회 접근자 : {current_user["USER_ID"]}')
        # query 파라메터의 경우 parse_args() 실행시 설정된 유효성 검사가 별도로 진행됨
        args = _Schema.board_list_params.parse_args()
        (board_list, totalcount) = BoardService().get_board_list(args['start_row'], args['row_per_page'])
        # marshal_with 에 등록된 모델과 일치하지 않는 필드는 매핑되지 않음
        return {'totalcount': totalcount, 'board_list': board_list}, int(HTTPStatus.OK)

    # request : Model을 사용할 경우 validate 옵션을 설정해야 설정된 유효성 검사를 할 수 있음
    #           RESTX_VALIDATE 설정으로 기본값을 변경 할 수 있음
    @jwt_required()
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.system_error_model)
    @board_sample.expect(_Schema.board_save_model, validate=True)
    @board_sample.marshal_with(_Schema.board_save_result_model, code=int(HTTPStatus.OK), description='게시물 등록결과')
    def post(self):
        """
        게시물 등록
        :return:
        :rtype:
        """
        # request를 사용하지 않고, Namespace에서 payload로 JSON 객체를 가져올 수 있음
        args = board_sample.payload
        # user_id 정보는 파라메터가 아닌 flask_jwt_extended 모듈의 current_user 정보에서 가져옮
        result = BoardService().save_board(None, args['title'], args['contents'], current_user['USER_ID'])
        return {'result': 'Success', 'board_seq': result}, int(HTTPStatus.OK)


@board_sample.route('/<int:board_seq>')
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.error_model)
@board_sample.response(int(HTTPStatus.NOT_FOUND), '게시물 없음', app.system_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.system_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.system_error_model)
class BoardSample(Resource):
    """
    게시물 한건에 대한 조회, 수정, 삭제
    """
    @board_sample.marshal_with(_Schema.board_detail_model, code=int(HTTPStatus.OK), description='게시물 상세정보')
    def get(self, board_seq):
        """
        게시물 상세조회
        :param board_seq:
        :type board_seq:
        :return:
        :rtype:
        """
        result = BoardService().get_board_by_seq(board_seq)
        if not result:
            raise NotFound('게시물이 존재하지 않습니다.')
        return result, int(HTTPStatus.OK)

    @jwt_required()
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.system_error_model)
    @board_sample.expect(_Schema.board_save_model, validate=True)
    @board_sample.marshal_with(_Schema.board_detail_model, code=int(HTTPStatus.OK), description='게시물 수정결과')
    def put(self, board_seq):
        """
        게시물 수정
        :param board_seq:
        :type board_seq:
        :return:
        :rtype:
        """
        args = board_sample.payload
        board_service = BoardService()
        board_service.save_board(board_seq, args['title'], args['contents'], current_user['USER_ID'])
        result = board_service.get_board_by_seq(board_seq)
        return result, int(HTTPStatus.OK)

    @jwt_required()
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.system_error_model)
    @board_sample.marshal_with(_Schema.board_delete_result_model, code=int(HTTPStatus.OK), description='게시물 삭제결과')
    def delete(self, board_seq):
        """
        게시물 삭제
        :param board_seq:
        :type board_seq:
        :return:
        :rtype:
        """
        result = BoardService().delete_boards([board_seq])
        if result < 1:
            raise NotFound('게시물이 존재하지 않습니다.')
        return {'result': 'Success', 'deleted_count': result}, int(HTTPStatus.OK)


@board_sample.route('/fileupload')
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.error_model)
@board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.system_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.system_error_model)
@board_sample.response(int(HTTPStatus.REQUEST_ENTITY_TOO_LARGE), '파일 업로드 용량 초과', app.system_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.system_error_model)
class FileUploadPost(Resource):
    """
    파일 업로드 및 임시 저장정보 반환
    flask-restx 에서는 여러파일을 한번에 업로드하는것을 기본적으로는 지원하지 않는것으로 보임
    https://github.com/python-restx/flask-restx/issues/177
    """
    @jwt_required()
    @board_sample.expect(_Schema.file_upload_params, validate=True)
    @board_sample.marshal_with(_Schema.file_upload_result_model, code=int(HTTPStatus.OK), description='파일 업로드 결과')
    def post(self):
        """
        파일 업로드
        :return:
        :rtype:
        """
        args = _Schema.file_upload_params.parse_args()
        uploaded_file = args['file']
        # 원본파일명
        filename = uploaded_file.filename
        # 임시저장 디렉토리 설정
        file_tmp_path = PathConfig[g.env_val]['file_tmp_path']
        file_full_path = PathConfig[g.env_val]['file_upload_home'] + os.path.sep + file_tmp_path
        os.makedirs(file_full_path, exist_ok=True)
        # 임시파일명
        file_ext = filename.split('.')[(len(filename.split('.')) - 1)] if len(filename.split('.')) > 1 else ''
        file_tmp_name = str(uuid.uuid4().hex) + '.' + file_ext
        # 업로드 파일 임시저장
        tmp_file_full_path = os.path.join(file_full_path, file_tmp_name)
        uploaded_file.save(tmp_file_full_path)
        return {'result': 'Success', 'file_org_name': filename, 'file_tmp_path': file_tmp_path, 'file_tmp_name': file_tmp_name}, int(HTTPStatus.OK)


@board_sample.route('/<int:board_seq>/file')
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.error_model)
@board_sample.response(int(HTTPStatus.NOT_FOUND), '게시물 없음', app.system_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.system_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.system_error_model)
class BoardFilePost(Resource):
    @board_sample.marshal_with(_Schema.file_list_model, code=int(HTTPStatus.OK), description='게시물의 파일목록')
    def get(self, board_seq):
        """
        게시물의 파일목록 조회
        :param board_seq:
        :type board_seq:
        :return:
        :rtype:
        """
        result = BoardService().get_board_by_seq(board_seq)
        if not result:
            raise NotFound('게시물이 존재하지 않습니다.')
        # 파일 목록 조회
        result = BoardService().get_board_file_list(board_seq)
        return {'board_seq': board_seq, 'file_list': result}, int(HTTPStatus.OK)

    @jwt_required()
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.system_error_model)
    @board_sample.expect(_Schema.file_save_list_model, validate=True)
    @board_sample.marshal_with(_Schema.file_save_result_model, code=int(HTTPStatus.OK), description='게시물에 파일정보 저장결과')
    def post(self, board_seq):
        """
        게시물에 파일정보 저장
        :param board_seq:
        :type board_seq:
        :return:
        :rtype:
        """
        result = BoardService().get_board_by_seq(board_seq)
        if not result:
            raise NotFound('게시물이 존재하지 않습니다.')
        args = board_sample.payload
        # 파일 목록을 변수에 맞춰 매핑
        file_seqs = []
        file_org_names = []
        file_tmp_names = []
        file_tmp_paths = []
        if 'file_list' in args and len(args['file_list']) > 0:
            # 파일 목록 매핑
            for file_info in args['file_list']:
                file_seqs.append(file_info['file_seq'])
                file_org_names.append(file_info['file_org_name'])
                file_tmp_names.append(file_info['file_tmp_name'])
                file_tmp_paths.append(file_info['file_tmp_path'])
            # 파일정보 저장
            BoardService().save_board_file(board_seq, file_seqs, file_org_names, file_tmp_names, file_tmp_paths, current_user['USER_ID'])
        # 파일 목록 조회
        result = BoardService().get_board_file_list(board_seq)
        return {'result': 'Success', 'board_seq': board_seq, 'file_list': result}, int(HTTPStatus.OK)
