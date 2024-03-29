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
from ..enums import BoardsCode
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
    schemas에서 구성한 Model을 사용하기 위해서는 add_model 로 최소 한번은 등록되어야함
    fields.Nested에 연결된 모든 Model이 등록되어 있어야 Swagger 문서가 정상적으로 생성됨
    예) a = Model('a', {})
        b = Model('b', {'ref': fields.Nested(a)})
        c.add_model(a)
        d = c.add_model(b)
        e.marshal_with(d, code=200, description='b')
    다른 Namespace에서 모델이 등록된것을 재사용하는 경우 add_model을 생략할 수 있음
    예) f.marshal_with(e.d, code=200, description='b')
    다른 Namespace에 등록된 모델을 다시 등록해도 됨
    예) g = f.add_mode(a)
        f.marshal_with(g, code=200, description='a')
    add_model() 로 등록된 모델은 등록한 변수를 사용하지 않고 생성 시 사용한 변수로 expect, response, marshal_with 에서 매핑 할 수 있음
    예) f.marshal_with(a, code=200, description='a')
    """
    # 게시물 상세 모델
    board_sample.add_model(BoardSchemas.wildcard_multi_model.name, BoardSchemas.wildcard_multi_model)
    board_save_model = board_sample.add_model(BoardSchemas.board_save_model.name, BoardSchemas.board_save_model)
    board_detail_model = board_sample.add_model(BoardSchemas.board_detail_model.name, BoardSchemas.board_detail_model)
    # 게시물 등록 결과
    board_save_result_model = board_sample.add_model(BoardSchemas.board_save_result_model.name, BoardSchemas.board_save_result_model)
    # 게시물 삭제 결과
    board_delete_result_model = board_sample.add_model(BoardSchemas.board_delete_result_model.name, BoardSchemas.board_delete_result_model)
    # 게시물 목록 모델
    board_sample.add_model(BoardSchemas.board_detail_model_for_list.name, BoardSchemas.board_detail_model_for_list)
    board_list_model = board_sample.add_model(BoardSchemas.board_list_model.name, BoardSchemas.board_list_model)
    # 파일 업로드 파라메터
    # action='append'를 사용하면 여러 파일을 동시에 업로드 할 수 있음
    file_upload_params = board_sample.parser()
    file_upload_params.add_argument('file', location='files', type=FileStorage, required=True, help='업로드 파일', action='append')
    # 파일 업로드 결과 모델
    board_sample.add_model(BoardSchemas.file_model.name, BoardSchemas.file_model)
    file_upload_result_model = board_sample.add_model(BoardSchemas.file_upload_result_model.name, BoardSchemas.file_upload_result_model)
    # 업로드된 파일정보 저장 모델
    file_save_model = board_sample.add_model(BoardSchemas.file_save_model.name, BoardSchemas.file_save_model)
    # 파일정보 상세
    file_detail_model = board_sample.add_model(BoardSchemas.file_detail_model.name, BoardSchemas.file_detail_model)
    # 실제 파라메터로 넘길 파일정보 목록 모델
    file_save_list_model = board_sample.add_model(BoardSchemas.file_save_list_model.name, BoardSchemas.file_save_list_model)
    # 파일 목록 모델
    file_list_model = board_sample.add_model(BoardSchemas.file_list_model.name, BoardSchemas.file_list_model)
    # 파일정보 저장 결과 모델
    file_save_result_model = board_sample.add_model(BoardSchemas.file_save_result_model.name, BoardSchemas.file_save_result_model)


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
    @board_sample.expect(common_list_params, validate=True)
    # response : marshal_with를 사용하면 결과값에 대한 모델매핑과 apidoc을 한번에 작성 할 수 있음
    @board_sample.marshal_with(_Schema.board_list_model, code=int(HTTPStatus.OK), description='게시물 목록')
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
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
    @board_sample.expect(_Schema.board_save_model, validate=True)
    @board_sample.marshal_with(_Schema.board_save_result_model, code=int(HTTPStatus.OK), description='게시물 등록결과')
    @board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
    def post(self):
        """
        게시물 등록
        :return:
        :rtype:
        """
        # request를 사용하지 않고, Namespace에서 payload로 JSON 객체를 가져올 수 있음
        args = board_sample.payload
        # user_id 정보는 파라메터가 아닌 flask_jwt_extended 모듈의 current_user 정보에서 가져옮
        result = BoardService().save_board(None, args['boards_code'], args['title'], args['contents'], args['add_fields'], current_user['USER_ID'])
        return {'result': 'Success', 'board_seq': result}, int(HTTPStatus.OK)


@board_sample.route('/<int:board_seq>')
@board_sample.doc(security='bearer_auth')
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.NOT_FOUND), '게시물 없음', app.default_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
class BoardSample(Resource):
    """
    게시물 한건에 대한 조회, 수정, 삭제
    """
    @jwt_required(optional=True)
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
        board_service.save_board(board_seq, args['boards_code'], args['title'], args['contents'], args['add_fields'], current_user['USER_ID'])
        result = board_service.get_board_by_seq(board_seq)
        return result, int(HTTPStatus.OK)

    @jwt_required()
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


@board_sample.route('/<boards_code:boards_code>')
@board_sample.route('/boards_code/<boards_code:boards_code>', doc={'description': '명시적으로 URL에 /board/boards_code/{boards_code}를 사용 할 수 있음'})
@board_sample.param('boards_code', enum=list([v.name for v in BoardsCode]))
@board_sample.doc(security='bearer_auth')
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
class BoardListByBoardsCode(Resource):
    """
    게시물 BOARDS_CODE 별 목록 조회
    """
    @jwt_required(optional=True)
    @board_sample.expect(common_list_params, validate=True)
    @board_sample.marshal_with(_Schema.board_list_model, code=int(HTTPStatus.OK), description='게시물 목록')
    def get(self, boards_code):
        """
        BOARDS_CODE 별 목록 조회
        :param boards_code:
        :type boards_code:
        :return:
        :rtype:
        """
        # JWT TOKEN 이 있는경우 해당 정보를 로그로 남김
        current_identity = get_jwt_identity()
        if current_identity:
            board_sample.logger.info(f'게시물 BOARDS_CODE 별 목록 조회 접근자 : {current_user["USER_ID"]}')
        args = common_list_params.parse_args()
        (board_list, totalcount) = BoardService().get_board_list_by_boards_code(args['start_row'], args['row_per_page'], boards_code)
        return {'totalcount': totalcount, 'board_list': board_list}, int(HTTPStatus.OK)


@board_sample.route('/board_seqs/<int_list:board_seqs>')
@board_sample.param('board_seqs', example='1,2,3')
@board_sample.doc(security='bearer_auth')
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
class BoardListByBoardSeqs(Resource):
    """
    선택된 BOARD_SEQ에 따른 목록 조회, 삭제
    """
    @jwt_required(optional=True)
    @board_sample.marshal_with(_Schema.board_list_model, code=int(HTTPStatus.OK), description='게시물 목록')
    def get(self, board_seqs):
        """
        선택된 BOARD_SEQ에 해당하는 목록 조회
        :param board_seqs:
        :type board_seqs:
        :return:
        :rtype:
        """
        # JWT TOKEN 이 있는경우 해당 정보를 로그로 남김
        current_identity = get_jwt_identity()
        if current_identity:
            board_sample.logger.info(f'게시물 BOARD_SEQ에 따른 목록 조회 접근자 : {current_user["USER_ID"]}')
        (board_list, totalcount) = BoardService().get_board_list_by_board_seqs(board_seqs)
        return {'totalcount': totalcount, 'board_list': board_list}, int(HTTPStatus.OK)

    @jwt_required()
    @board_sample.marshal_with(_Schema.board_delete_result_model, code=int(HTTPStatus.OK), description='게시물 삭제결과')
    def delete(self, board_seqs):
        """
        선택된 BOARD_SEQ에 해당하는 목록 삭제
        :param board_seqs:
        :type board_seqs:
        :return:
        :rtype:
        """
        result = BoardService().delete_boards(board_seqs)
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
    consumes 관련 설정 버그 : https://github.com/python-restx/flask-restx/issues/471
    """
    @jwt_required()
    @board_sample.expect(_Schema.file_upload_params, validate=True)
    @board_sample.marshal_with(_Schema.file_upload_result_model, code=int(HTTPStatus.OK), description='파일 업로드 결과')
    def post(self):
        """
        파일 업로드
        action='append' 인경우 args['file'] 반환값이 [] 이므로 주의할것!!
        :return:
        :rtype:
        """
        args = _Schema.file_upload_params.parse_args()
        uploaded_file = args['file']
        uploaded_file_list = []
        for file_obj in uploaded_file:
            uploaded_file_list.append(self._file_save(file_obj))
        return {'result': 'Success', 'files': uploaded_file_list}, int(HTTPStatus.OK)

    @staticmethod
    def _file_save(uploaded_file):
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
        return {'file_org_name': filename, 'file_tmp_path': file_tmp_path, 'file_tmp_name': file_tmp_name}


@board_sample.route('/<int:board_seq>/file')
@board_sample.doc(security='bearer_auth')
@board_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.NOT_FOUND), '게시물 없음', app.default_error_model)
@board_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@board_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
class BoardFilePost(Resource):
    @jwt_required(optional=True)
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
