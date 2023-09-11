import logging
import os
import traceback
from http import HTTPStatus
from pathlib import Path

from flask import Flask, Blueprint, g
from flask_restx import Api, apidoc, fields
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, MethodNotAllowed

from .configs import PROJECT_ID
from .services import Sqlite3Service
from .utils import err_log

# env 설정
env_val = None
# logger 설정
logger = logging.getLogger(PROJECT_ID)
# Flask 생성
app = Flask(__name__)
# api 기본 URL 변경 : /api/v1
api_path = Blueprint('api', __name__, url_prefix='/api/v1')
# flask_restx 설정
# doc 옵션으로 apidoc url path 변경, False 값을 추가하면 404 발생
# @api.documentation 을 사용하여 별도 처리할 수 있음
api = Api(
    api_path,
    version='0.1',
    title='flask-restx Test',
    doc='/docs'
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


# 등록된 순서대로 처리되므로 500 오류를 가장 마지막에 등록할것!!
@api.errorhandler(BadRequest)
@api.marshal_with(error_model, code=int(HTTPStatus.BAD_REQUEST), description='400 오류')
def handle_400_exception(error):
    err_log(logger, error, __name__, traceback.format_exc(), '400 Bad Request')
    return {'message': str(error)}, int(HTTPStatus.BAD_REQUEST)


@api.errorhandler(FileNotFoundError)
@api.marshal_with(system_error_model, code=int(HTTPStatus.NOT_FOUND), description='404 오류')
def handle_404_exception(error):
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
    from .apis import board_sample
    api_param.add_namespace(board_sample)


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
        # router 설정
        register_router(api)
        # Sqlite 초기 설정
        Sqlite3Service()
    except Exception as e:
        err_log(logger, e, __name__, traceback.format_exc(), 'App start error!!!')
