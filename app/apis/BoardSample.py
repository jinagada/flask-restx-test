import logging
import os
import uuid
from http import HTTPStatus

from flask import g
from flask_babel import gettext
from flask_jwt_extended import jwt_required, current_user, get_jwt_identity
from flask_restx import Namespace, Resource
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import NotFound

import app
from ..configs import PathConfig, PROJECT_ID
from ..schemas import common_list_params, BoardSchemas
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
    Schema dic 만 별로 파일로 분리
    """
    # 게시물 상세 모델
    board_save_model = board_sample.model('BoardSave', BoardSchemas.board_save_schema)
    board_detail_model = board_sample.inherit('BoardDetail', board_save_model, BoardSchemas.board_detail_schema)
    # 게시물 등록 결과
    board_save_result_model = board_sample.model('BoardSaveResult', BoardSchemas.board_save_result_schema)
    # 게시물 삭제 결과
    board_delete_result_model = board_sample.model('BoardDeleteResult', BoardSchemas.board_delete_result_schema)
    # 게시물 목록 모델
    board_list_model = board_sample.model('BoardListResult', BoardSchemas.board_list_schema)
    # 파일 업로드 파라메터
    # 아직은 다른 type의 파라메터를 추가하거나 여러 파일 동시 업로드는 지원하지 않아보임
    # 한번에 하나의 파일만 업로드 가능함
    file_upload_params = board_sample.parser()
    file_upload_params.add_argument('file', location='files', type=FileStorage, required=True, help='업로드 파일')
    # 파일 업로드 결과 모델
    file_upload_result_model = board_sample.model('FileUploadResult', BoardSchemas.file_upload_result_schema)
    # 업로드된 파일정보 저장 모델
    file_save_model = board_sample.model('FileSave', BoardSchemas.file_save_schema)
    # 파일정보 상세
    file_detail_model = board_sample.model('FileDetail', BoardSchemas.file_detail_schema)
    # 실제 파라메터로 넘길 파일정보 목록 모델
    file_save_list_model = board_sample.model('FileSaveList', BoardSchemas.file_save_list_schema)
    # 파일 목록 모델
    file_list_model = board_sample.model('FileList', BoardSchemas.file_list_schema)
    # 파일정보 저장 결과 모델
    file_save_result_model = board_sample.inherit('FileSaveResult', file_list_model, BoardSchemas.file_save_result_schema)


# Namespace에 설정된 path값 이후의 URL을 route에 추가할 수 있음
@board_sample.route('')
@board_sample.doc(security='bearer_auth')
# 모든 METHOD에 동일한 code가 사용되는 경우 class에 설정하면 한번에 적용 가능함
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
class BoardPost(Resource):
    """
    게시물 목록 조회, 게시물 등록
    """
    # request : query 파라메터에서도 validate 옵션을 사용하면 설정된 유효성 검사가 function 진입전에 실행됨
    @jwt_required(optional=True)
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
    @board_sample.expect(common_list_params, validate=True)
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
        args = common_list_params.parse_args()
        (board_list, totalcount) = BoardService().get_board_list(args['start_row'], args['row_per_page'])
        # marshal_with 에 등록된 모델과 일치하지 않는 필드는 매핑되지 않음
        return {'totalcount': totalcount, 'board_list': board_list}, int(HTTPStatus.OK)

    # request : Model을 사용할 경우 validate 옵션을 설정해야 설정된 유효성 검사를 할 수 있음
    #           RESTX_VALIDATE 설정으로 기본값을 변경 할 수 있음
    @jwt_required()
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
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
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.NOT_FOUND), '게시물 없음', app.default_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
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
            raise NotFound(gettext(u'게시물이 존재하지 않습니다.'))
        return result, int(HTTPStatus.OK)

    @jwt_required()
    @board_sample.doc(security='bearer_auth')
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
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
    @board_sample.doc(security='bearer_auth')
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
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
            raise NotFound(gettext(u'게시물이 존재하지 않습니다.'))
        return {'result': 'Success', 'deleted_count': result}, int(HTTPStatus.OK)


@board_sample.route('/fileupload')
@board_sample.doc(security='bearer_auth')
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.REQUEST_ENTITY_TOO_LARGE), '파일 업로드 용량 초과', app.default_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
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
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.NOT_FOUND), '게시물 없음', app.default_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
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
            raise NotFound(gettext(u'게시물이 존재하지 않습니다.'))
        # 파일 목록 조회
        result = BoardService().get_board_file_list(board_seq)
        return {'board_seq': board_seq, 'file_list': result}, int(HTTPStatus.OK)

    @jwt_required()
    @board_sample.doc(security='bearer_auth')
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
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
            raise NotFound(gettext(u'게시물이 존재하지 않습니다.'))
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
