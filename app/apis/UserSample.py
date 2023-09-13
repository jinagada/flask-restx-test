from http import HTTPStatus

from flask_jwt_extended import create_access_token
from flask_restx import Namespace, Resource, fields
from werkzeug.exceptions import Unauthorized

import app
from ..services import UsersService

login_sample = Namespace(
    path='/login',
    name='Login Sample',
    description='JWT 로그인 예제'
)


class _Schema:
    login_model = login_sample.model('Login', {
        'user_id': fields.String(description='사용자ID', example='UserId', required=True, min_length=5),
        'password': fields.String(description='비밀번호', example='12#$qw', required=True, min_length=5),
    })
    jwt_token_model = login_sample.model('JWTToken', {
        'access_token': fields.String(description='JWT Access Token', example='JWT TOKEN')
    })


@login_sample.route('')
@login_sample.response(int(HTTPStatus.UNAUTHORIZED), '인증 오류', app.error_model)
@login_sample.response(int(HTTPStatus.METHOD_NOT_ALLOWED), 'METHOD 오류', app.system_error_model)
@login_sample.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), '시스템 오류', app.system_error_model)
class LoginPost(Resource):
    """
    사용자 로그인
    """
    @login_sample.expect(_Schema.login_model, validate=True)
    @login_sample.marshal_with(_Schema.jwt_token_model, code=int(HTTPStatus.OK), description='JWT TOKEN 정보')
    def post(self):
        args = login_sample.payload
        user_info = UsersService().get_user_by_id(args['user_id'])
        if user_info:
            if user_info['USER_PW'] != args['password']:
                raise Unauthorized('사용자 정보가 일치하지 않습니다.')
            else:
                return {'access_token': create_access_token(identity=user_info)}
        else:
            raise Unauthorized('사용자 정보가 일치하지 않습니다.')
