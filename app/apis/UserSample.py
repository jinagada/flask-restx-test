import logging
from datetime import timedelta
from http import HTTPStatus

from flask_babel import gettext
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, current_user, get_jwt
from flask_restx import Namespace, Resource
from werkzeug.exceptions import Unauthorized, NotFound

import app
from ..configs import PROJECT_ID
from ..schemas import common_list_params, UserSchemas
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
    login_model = login_sample.model('Login', UserSchemas.login_schema)
    jwt_token_login_model = login_sample.model('JWTTokenLogin', UserSchemas.jwt_token_login_schema)
    jwt_token_refresh_model = login_sample.model('JWTTokenRefresh', UserSchemas.jwt_token_refresh_schema)
    # 사용자 상세 모델
    user_save_model = user_sample.model('UserSave', UserSchemas.user_save_schema)
    user_detail_model = user_sample.inherit('UserDetail', user_save_model, UserSchemas.user_detail_schema)
    # 사용자 등록 결과
    user_save_result_model = user_sample.model('UserSaveResult', UserSchemas.user_save_result_schema)
    # 사용자 삭제 결과
    user_delete_result_model = user_sample.model('UserDeleteResult', UserSchemas.user_delete_result_schema)
    # 사용자 목록 모델
    user_list_model = user_sample.model('UserListResult', UserSchemas.user_list_schema)
    # current_user 및 권한 모델
    jwt_login_info_model = login_sample.model('JWTLoginInfo', UserSchemas.jwt_login_info_schema)


@login_sample.route('')
@login_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
@login_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@login_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
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
                raise Unauthorized(gettext(u'사용자 정보가 일치하지 않습니다.'))
            else:
                # 권한정보 추가
                if user_info['SEQ'] == 1:
                    additional_claims = {'aud': 'ADMIN'}
                else:
                    additional_claims = {'aud': 'USER'}
                # timedelta를 사용하여 만료기간을 설정할 수 있음
                return {
                    # access_token : 5분(사용자의 인증정보 및 권한 정보를 가진 짧은 주기의 토큰으로 임시저장소에 저장됨)
                    'access_token': create_access_token(identity=user_info, additional_claims=additional_claims, expires_delta=timedelta(minutes=5)),
                    # refresh_token : 1시간(사용자의 인증에 대한 갱신을 위한 긴 주기의 토큰으로 안전한 저장소에 저장됨)
                    'refresh_token': create_refresh_token(identity=user_info, expires_delta=timedelta(hours=1))
                }, int(HTTPStatus.OK)
        else:
            raise Unauthorized(gettext(u'사용자 정보가 일치하지 않습니다.'))

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
@refresh_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
@refresh_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@refresh_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
class RefreshPost(Resource):
    """
    JWT TOKEN Refresh
    """
    # We are using the `refresh=True` options in jwt_required to only allow
    # refresh tokens to access this route.
    # Refresh Token 이 아닌경우 WrongTokenError 발생
    # refresh=True 옵션이 없는경우 기본적으로 access_token만을 허용함
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
@user_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.default_error_model)
@user_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
@user_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@user_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
class UserPost(Resource):
    """
    사용자 목록, 등록
    """
    @jwt_required()
    @user_sample.expect(common_list_params, validate=True)
    @user_sample.marshal_with(_Schema.user_list_model, code=int(HTTPStatus.OK), description='사용자 목록')
    def get(self):
        """
        사용자 목록 조회
        :return:
        :rtype:
        """
        args = common_list_params.parse_args()
        (user_list, totalcount) = UsersService().get_user_list(args['start_row'], args['row_per_page'])
        user_sample.logger.info(app.api.models.keys())
        user_sample.logger.info(user_sample.models.keys())
        user_sample.logger.info(login_sample.models.keys())
        return {'user_list': user_list, 'totalcount': totalcount}, int(HTTPStatus.OK)

    @admin_required()
    @user_sample.response(int(HTTPStatus.FORBIDDEN), '권한 오류', app.default_error_model)
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
@user_sample.response(int(HTTPStatus.BAD_REQUEST), '파라메터 오류', app.default_error_model)
@user_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.default_error_model)
@user_sample.response(int(HTTPStatus.NOT_FOUND), '사용자 없음', app.default_error_model)
@user_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.default_error_model)
@user_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.default_error_model)
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
            raise Unauthorized(gettext(u'로그인한 사용자의 정보만 조회 할 수 있습니다.'))
        result = UsersService().get_user_by_seq(user_seq)
        if not result:
            raise NotFound(gettext(u'사용자가 존재하지 않습니다.'))
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
            raise Unauthorized(gettext(u'로그인한 사용자의 정보만 수정 할 수 있습니다.'))
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
            raise Unauthorized(gettext(u'로그인한 사용자의 정보만 삭제 할 수 있습니다.'))
        result = UsersService().check_delete_users([user_seq])
        return {'result': 'Success', 'deleted_count': result}, int(HTTPStatus.OK)
