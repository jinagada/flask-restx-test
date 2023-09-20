import logging
import os
import traceback
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path

from flask import Flask, Blueprint, g, request
from flask_babel import Babel, gettext
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import NoAuthorizationError, UserLookupError, WrongTokenError
from flask_restx import Api, apidoc, fields
from jwt.exceptions import ExpiredSignatureError
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, MethodNotAllowed, NotFound, Unauthorized, Forbidden

from .configs import PROJECT_ID
from .services import Sqlite3Service, UsersService
from .utils import err_log

# env 설정
env_val = None
# logger 설정
logger = logging.getLogger(PROJECT_ID)
# Flask 생성
app = Flask(__name__)
# Babel 생성
babel = Babel()
# Babel locale 기본값을 한국어(ko)로 설정
app.config['BABEL_DEFAULT_LOCALE'] = 'ko'
# JWT 설정
# JWT_SECRET_KEY 값은 암호화에 사용되므로 32자 이상의 해시값을 사용할것!
app.config["JWT_SECRET_KEY"] = "3c15ea2011adbc1f764c956ed9f0bbb6dc51d15b815590e45bfb52cc0fc15d2d"
jwt = JWTManager(app)
# api 기본 URL 변경 : /api/v1
api_path = Blueprint('api', __name__, url_prefix='/api/v1')
# flask_restx 설정
# authorizations 설정을 하면 상단에 "Authorize" 버튼이 나타남
authorizations = {
    'bearer_auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'bearerFormat': 'JWT',
        'description': '/login 을 사용하여 얻은 access_token 을 사용\n예) Bearer <JWT TOKEN>'
    }
}
# doc 옵션으로 apidoc url path 변경, False 값을 추가하면 404 발생
# @api.documentation 을 사용하여 별도 처리할 수 있음
# security 설정을 하면 전체 API 목록에 좌물쇠 버튼이 나타남
api = Api(
    api_path,
    version='0.1',
    title='flask-restx Test',
    doc='/docs',
    authorizations=authorizations
)
# Flask에 Blueprint 등록
app.register_blueprint(api_path)
# 파일업로드 크기 설정(50MB)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
# error 모델 설정
error_model = api.model('ErrorMsg', {
    'erros': fields.Raw(description='오류 내용', example='dict 형식의 오류내용이 포함됨'),
    'message': fields.String(description='오류 메시지', example='오류 메시지')
})
# 500 에러 모델 설정
system_error_model = api.model('SystemErrorMsg', {
    'message': fields.String(description='오류 메시지', example='오류 메시지')
})


@api.documentation
def api_doc():
    """
    apidoc.ui_for(api)는 기본 UI 사용
    :return:
    :rtype:
    """
    if g.env_val == 'prd':
        raise NotFound(gettext(u'운영에서는 문서를 제공하지 않음'))
    return apidoc.ui_for(api)


@app.before_request
def init_global():
    """
    current_app or g 변수 설정
    before_app_request 가 먼저 호출되고 그 다음 before_request 가 호출됨
    before_app_request 는 Blueprint 에만 존재함
    """
    if 'env_val' not in g:
        g.env_val = env_val


# Flask 오류 설정
@app.errorhandler(404)
def handle_404_error(error):
    """
    실제 URL이 없는경우에 대한 처리
    :param error:
    :type error:
    :return:
    :rtype:
    """
    err_log(logger, error, __name__, traceback.format_exc(), '404 File Not Found')
    return {'message': str(error)}, int(HTTPStatus.NOT_FOUND)


# 등록된 순서대로 처리되므로 500 오류를 가장 마지막에 등록할것!!
@api.errorhandler(BadRequest)
@api.marshal_with(error_model, code=int(HTTPStatus.BAD_REQUEST), description='400 오류')
def handle_400_exception(error):
    err_log(logger, error, __name__, traceback.format_exc(), '400 Bad Request')
    return {'message': str(error)}, int(HTTPStatus.BAD_REQUEST)


# 여러 오류를 등록하여 하나로 처리 할 수 있음
@api.errorhandler(Unauthorized)
@api.errorhandler(NoAuthorizationError)
@api.errorhandler(ExpiredSignatureError)
@api.errorhandler(WrongTokenError)
@api.errorhandler(UserLookupError)
@api.marshal_with(system_error_model, code=int(HTTPStatus.UNAUTHORIZED), description='401 오류')
def handle_401_exception(error):
    err_log(logger, error, __name__, traceback.format_exc(), '401 Unauthorized')
    return {'message': str(error)}, int(HTTPStatus.UNAUTHORIZED)


@api.errorhandler(Forbidden)
@api.marshal_with(system_error_model, code=int(HTTPStatus.FORBIDDEN), description='403 오류')
def handle_403_exception(error):
    err_log(logger, error, __name__, traceback.format_exc(), '403 Forbidden')
    return {'message': str(error)}, int(HTTPStatus.FORBIDDEN)


@api.errorhandler(NotFound)
@api.marshal_with(system_error_model, code=int(HTTPStatus.NOT_FOUND), description='404 오류')
def handle_404_exception(error):
    """
    소스에서 임의로 발생시킨 Not Found
    :param error:
    :type error:
    :return:
    :rtype:
    """
    err_log(logger, error, __name__, traceback.format_exc(), '404 File Not Found')
    return {'message': str(error)}, int(HTTPStatus.NOT_FOUND)


@api.errorhandler(MethodNotAllowed)
@api.marshal_with(system_error_model, code=int(HTTPStatus.METHOD_NOT_ALLOWED), description='405 오류')
def handle_405_exception(error):
    err_log(logger, error, __name__, traceback.format_exc(), '405 Method Not Allowed')
    return {'message': str(error)}, int(HTTPStatus.METHOD_NOT_ALLOWED)


@api.errorhandler(RequestEntityTooLarge)
@api.marshal_with(system_error_model, code=int(HTTPStatus.REQUEST_ENTITY_TOO_LARGE), description='413 오류')
def handle_413_exception(error):
    err_log(logger, error, __name__, traceback.format_exc(), '413 Request Entity Too Large')
    return {'message': str(error)}, int(HTTPStatus.REQUEST_ENTITY_TOO_LARGE)


@api.errorhandler(Exception)
@api.marshal_with(system_error_model, code=int(HTTPStatus.INTERNAL_SERVER_ERROR), description='500 오류')
def handle_500_exception(error):
    err_log(logger, error, __name__, traceback.format_exc(), '500 Server Error')
    return {'message': str(error)}, int(HTTPStatus.INTERNAL_SERVER_ERROR)


@jwt.user_identity_loader
def user_identity_loader(user):
    """
    # Register a callback function that takes whatever object is passed in as the
    # identity when creating JWTs and converts it to a JSON serializable format.

    로그인 처리 후 JWT 객체에 등록된 사용자 정보 중 SEQ 반환
    :param user:
    :type user:
    :return:
    :rtype:
    """
    return user['SEQ']


@jwt.user_lookup_loader
def user_lookup_loader(_jwt_header, jwt_data):
    """
    # Register a callback function that loads a user from your database whenever
    # a protected route is accessed. This should return any python object on a
    # successful lookup, or None if the lookup failed for any reason (for example
    # if the user has been deleted from the database).

    TOKEN 정보가 사용될 경우에만 호출됨
    TOKEN 만료시간이 지나면 ExpiredSignatureError 가 자동으로 발생함
    JWT 정보에서 실제 사용자 정보를 조회
    사용자 정보에 문제가 있는 경우에 대한 모든 처리가 가능함
    기본적으로 사용자 정보가 조회되지 않으면 오류(UserLookupError)를 발생시킴
    :param _jwt_header:
    :type _jwt_header:
    :param jwt_data:
    :type jwt_data:
    :return:
    :rtype:
    """
    # 만료시간 확인
    exp_timestamp = jwt_data['exp']
    now = datetime.now(timezone.utc)
    logger.info(f'now: {now}, exp: {datetime.utcfromtimestamp(exp_timestamp)}')
    # sub 정보에는 user_identity_loader에서 반환된 SEQ 값이 저장되어 있음
    identity = jwt_data['sub']
    user_info = UsersService().get_user_by_seq(identity)
    return user_info


def get_locale():
    """
    Flask-Babel locale 가져오기 설정
    request Header의 Accept-Language 값을 참고하도록 처리
    :return:
    :rtype:
    """
    locale_str = request.accept_languages.best_match(['ko', 'en', 'ja', 'zh'])
    logger.info(f'request Accept-Language: {locale_str}')
    return locale_str


def register_router(api_param):
    """
    API router 설정
    Flask 객체가 아닌 Api 객체에 Namespace가 등록됨
    :param api_param:
    :type api_param:
    :return:
    :rtype:
    """
    # Namespace 객체가 import 되어야함
    from .apis import login_sample, refresh_sample, board_sample, user_sample
    # 추가된 순서대로 Swagger 문서가 생성되는것으로 보임
    api_param.add_namespace(login_sample)
    api_param.add_namespace(refresh_sample)
    api_param.add_namespace(board_sample)
    api_param.add_namespace(user_sample)


def init_app(env):
    """
    App 초기 설정
    :return:
    :rtype:
    """
    try:
        # env별 설정
        global env_val
        if not env:
            raise ValueError('env is empty.')
        env_val = env
        # Log 디렉토리 생성
        home = str(Path(os.path.expanduser('~')))
        log_path = f'{home}/logs/{PROJECT_ID}'
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        # Logger 설정
        formatter = logging.Formatter('[%(levelname)s] [%(asctime)s] %(filename)s(%(lineno)d) : %(message)s')
        file_handler = logging.FileHandler(f'{log_path + os.sep + PROJECT_ID}.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG if env == 'local' else logging.INFO)
        # Flask-Babel 초기화 및 locale_selector 설정
        babel.init_app(app, locale_selector=get_locale)
        # router 설정
        register_router(api)
        # Sqlite 초기 설정
        Sqlite3Service()
    except Exception as e:
        err_log(logger, e, __name__, traceback.format_exc(), 'App start error!!!')
