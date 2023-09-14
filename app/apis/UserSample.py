import logging
from datetime import timedelta
from http import HTTPStatus

from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, current_user, get_jwt
from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.exceptions import Unauthorized, NotFound

import app
from ..configs import PROJECT_ID
from ..services import UsersService
from ..utils import admin_required

login_sample = Namespace(
    path='/login',
    name='Login Sample',
    description='JWT 로그인 예제'
)
login_sample.logger = logging.getLogger(f'{PROJECT_ID}.apis.LoginSample')
refresh_sample = Namespace(
    path='/refresh',
    name='Refresh Sample',
    description='JWT TOKEN Refresh 예제'
)
refresh_sample.logger = logging.getLogger(f'{PROJECT_ID}.apis.RefreshSample')
user_sample = Namespace(
    path='/user',
    name='User Sample',
    description='사용자 예제'
)
user_sample.logger = logging.getLogger(f'{PROJECT_ID}.apis.UserSample')


class _Schema:
    # 로그인 모델
    login_model = login_sample.model('Login', {
        'user_id': fields.String(description='사용자ID', example='UserId', required=True, min_length=5),
        'password': fields.String(description='비밀번호', example='12#$qw', required=True, min_length=5),
    })
    jwt_token_login_model = login_sample.model('JWTTokenLogin', {
        'access_token': fields.String(description='JWT Access Token', example='JWT TOKEN'),
        'refresh_token': fields.String(description='JWT Refresh Token', example='JWT TOKEN')
    })
    jwt_token_refresh_model = login_sample.model('JWTTokenRefresh', {
        'access_token': fields.String(description='JWT Access Token', example='JWT TOKEN')
    })
    # 사용자 목록 조회 파라메터
    user_list_params = reqparse.RequestParser()
    user_list_params.add_argument('start_row', location='args', type=int, required=True, default=0, help='시작행 번호')
    user_list_params.add_argument('row_per_page', location='args', type=int, required=True, default=10, help='화면당 행 수')
    # 사용자 상세 모델
    user_save_model = user_sample.model('UserSave', {
        'user_id': fields.String(description='사용자ID', example='UserId', attribute='USER_ID', required=True, min_length=5, max_length=20),
        'password': fields.String(description='비밀번호', example='Password', attribute='USER_PW', required=True, min_length=5, max_length=15),
        'user_name': fields.String(description='사용자명', example='UserName', attribute='USER_NAME', required=True, min_length=2, max_length=50)
    })
    user_detail_model = user_sample.inherit('UserDetail', user_save_model, {
        'user_seq': fields.Integer(description='사용자 번호', example=1, attribute='SEQ'),
        'rdate': fields.DateTime(description='등록일시', example='2023-09-06T14:42:06', attribute='RDATE'),
        'mdate': fields.DateTime(description='수정일시', example='2023-09-06T14:42:06', attribute='MDATE')
    })
    # 사용자 등록 결과
    user_save_result_model = user_sample.model('UserSaveResult', {
        'result': fields.String(description='결과', example='Success'),
        'user_seq': fields.Integer(description='사용자 번호', example=1)
    })
    # 사용자 삭제 결과
    user_delete_result_model = user_sample.model('UserDeleteResult', {
        'result': fields.String(description='결과', example='Success'),
        'deleted_count': fields.Integer(description='삭제된 사용자수', example=1)
    })
    # 사용자 목록 모델
    user_list_model = user_sample.model('UserListResult', {
        'totalcount': fields.Integer(description='사용자 전체 수', example=100),
        'user_list': fields.List(fields.Nested(user_detail_model, skip_none=True))
    })
    # current_user 및 권한 모델
    jwt_login_info_model = login_sample.model('JWTLoginInfo', {
        'current_user': fields.Nested(user_detail_model, skip_none=True),
        'claims': fields.Raw(description='JWT TOKEN 상세내용', example='dict 형식의 상세내용')
    })


@login_sample.route('')
@login_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.system_error_model)
@login_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.system_error_model)
@login_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.system_error_model)
class LoginPost(Resource):
    """
    사용자 로그인
    """
    @login_sample.expect(_Schema.login_model, validate=True)
    @login_sample.marshal_with(_Schema.jwt_token_login_model, code=int(HTTPStatus.OK), description='JWT TOKEN Login 정보')
    def post(self):
        """
        로그인
        :return:
        :rtype:
        """
        args = login_sample.payload
        user_info = UsersService().get_user_by_id(args['user_id'])
        if user_info:
            if user_info['USER_PW'] != args['password']:
                raise Unauthorized('사용자 정보가 일치하지 않습니다.')
            else:
                # 권한정보 추가
                if user_info['SEQ'] == 1:
                    additional_claims = {'aud': 'ADMIN'}
                else:
                    additional_claims = {'aud': 'USER'}
                # timedelta를 사용하여 만료기간을 설정할 수 있음
                return {
                    # access_token : 5분
                    'access_token': create_access_token(identity=user_info, additional_claims=additional_claims, expires_delta=timedelta(minutes=5)),
                    # refresh_token : 1시간
                    'refresh_token': create_refresh_token(identity=user_info, expires_delta=timedelta(hours=1))
                }, int(HTTPStatus.OK)
        else:
            raise Unauthorized('사용자 정보가 일치하지 않습니다.')

    @jwt_required()
    # security 설정으로 좌물쇠 버튼을 각각 따로 보여줄 수 있음
    @login_sample.doc(security='bearer_auth')
    @login_sample.marshal_with(_Schema.jwt_login_info_model, code=int(HTTPStatus.OK), description='JWT TOKEN Login 정보')
    def get(self):
        """
        로그인한 사용자의 current_user 및 JWT TOKEN 정보 확인
        :return:
        :rtype:
        """
        return {'current_user': current_user, 'claims': get_jwt()}, int(HTTPStatus.OK)


@refresh_sample.route('')
@refresh_sample.doc(security='bearer_auth')
@refresh_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.system_error_model)
@refresh_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.system_error_model)
@refresh_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.system_error_model)
class RefreshPost(Resource):
    """
    JWT TOKEN Refresh
    """
    # We are using the `refresh=True` options in jwt_required to only allow
    # refresh tokens to access this route.
    # Refresh Token 이 아닌경우 WrongTokenError 발생
    @jwt_required(refresh=True)
    @refresh_sample.marshal_with(_Schema.jwt_token_refresh_model, code=int(HTTPStatus.OK), description='JWT TOKEN Refresh 정보')
    def post(self):
        """
        JWT TOKEN Refresh
        :return:
        :rtype:
        """
        # access_token 의 identity 값은 사용자의 전체 정보이므로 get_jwt_identity 으로 JWT TOKEN 에서 가져온 sub 정보와는 다름
        # current_user 정보를 사용해야 하는것으로 보임
        # 권한정보 추가
        if current_user['SEQ'] == 1:
            additional_claims = {'aud': 'ADMIN'}
        else:
            additional_claims = {'aud': 'USER'}
        return {
            # access_token : 5분
            'access_token': create_access_token(identity=current_user, additional_claims=additional_claims, expires_delta=timedelta(minutes=5))
        }, int(HTTPStatus.OK)

    @jwt_required(refresh=True)
    @refresh_sample.marshal_with(_Schema.user_detail_model, code=int(HTTPStatus.OK), description='사용자 상세정보')
    def get(self):
        """
        Refresh TOKEN 정보 확인
        :return:
        :rtype:
        """
        return current_user, int(HTTPStatus.OK)


@user_sample.route('')
@user_sample.doc(security='bearer_auth')
@user_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.error_model)
@user_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.system_error_model)
@user_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.system_error_model)
@user_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.system_error_model)
class UserPost(Resource):
    """
    사용자 목록, 등록
    """
    @jwt_required()
    @user_sample.expect(_Schema.user_list_params, validate=True)
    @user_sample.marshal_with(_Schema.user_list_model, code=int(HTTPStatus.OK), description='사용자 목록')
    def get(self):
        """
        사용자 목록 조회
        :return:
        :rtype:
        """
        args = _Schema.user_list_params.parse_args()
        (user_list, totalcount) = UsersService().get_user_list(args['start_row'], args['row_per_page'])
        return {'user_list': user_list, 'totalcount': totalcount}, int(HTTPStatus.OK)

    @admin_required()
    @user_sample.response(int(HTTPStatus.FORBIDDEN), '권한 오류', app.system_error_model)
    @user_sample.expect(_Schema.user_save_model, validate=True)
    @user_sample.marshal_with(_Schema.user_save_result_model, code=int(HTTPStatus.OK), description='사용자 등록결과')
    def post(self):
        """
        사용자 등록
        :return:
        :rtype:
        """
        args = user_sample.payload
        result = UsersService().save_user(args['user_id'], args['password'], args['user_name'], None)
        return {'result': 'Success', 'user_seq': result}, int(HTTPStatus.OK)


@user_sample.route('/<int:user_seq>')
@user_sample.doc(security='bearer_auth')
@user_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.error_model)
@user_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.system_error_model)
@user_sample.response(int(HTTPStatus.NOT_FOUND), '사용자 없음', app.system_error_model)
@user_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.system_error_model)
@user_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.system_error_model)
class UserSample(Resource):
    """
    사용자 상세보기, 수정, 삭제
    """
    @jwt_required()
    @user_sample.marshal_with(_Schema.user_detail_model, code=int(HTTPStatus.OK), description='사용자 상세정보')
    def get(self, user_seq):
        """
        사용자 상세보기
        :param user_seq:
        :type user_seq:
        :return:
        :rtype:
        """
        if user_seq != current_user['SEQ']:
            raise Unauthorized('로그인한 사용자의 정보만 조회 할 수 있습니다.')
        result = UsersService().get_user_by_seq(user_seq)
        if not result:
            raise NotFound('사용자가 존재하지 않습니다.')
        return result, int(HTTPStatus.OK)

    @jwt_required()
    @user_sample.expect(_Schema.user_save_model, validate=True)
    @user_sample.marshal_with(_Schema.user_detail_model, code=int(HTTPStatus.OK), description='사용자 상세정보')
    def put(self, user_seq):
        """
        사용자 정보 수정
        :param user_seq:
        :type user_seq:
        :return:
        :rtype:
        """
        if user_seq != current_user['SEQ']:
            raise Unauthorized('로그인한 사용자의 정보만 수정 할 수 있습니다.')
        args = user_sample.payload
        user_service = UsersService()
        user_service.save_user(args['user_id'], args['password'], args['user_name'], user_seq)
        result = user_service.get_user_by_seq(user_seq)
        return result, int(HTTPStatus.OK)

    @jwt_required()
    @user_sample.marshal_with(_Schema.user_delete_result_model, code=int(HTTPStatus.OK), description='사용자 삭제결과')
    def delete(self, user_seq):
        """
        사용자 삭제
        :param user_seq:
        :type user_seq:
        :return:
        :rtype:
        """
        if user_seq != current_user['SEQ']:
            raise Unauthorized('로그인한 사용자의 정보만 삭제 할 수 있습니다.')
        result = UsersService().check_delete_users([user_seq])
        return {'result': 'Success', 'deleted_count': result}, int(HTTPStatus.OK)
