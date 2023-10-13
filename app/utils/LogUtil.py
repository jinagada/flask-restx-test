from datetime import datetime, timezone
from http import HTTPStatus

from flask import request
from werkzeug.exceptions import RequestEntityTooLarge


def err_log(logger, e, file_path, traceback_str=None, msg=None):
    """
    오류로그 출력
    :param logger:
    :param e:
    :param file_path: __name__ 를 사용하여 실행되고 있는 파일의 패키지 경로를 출력한다.
    :param traceback_str:
    :param msg:
    """
    # 오류 메시지 목록 생성
    error_msg_list = [f'{file_path} ERROR ========= START']
    if request:
        error_msg_list.append(f'{file_path} Call URL : {request.url if request.url else ""}')
        error_msg_list.append(f'{file_path} Call METHOD : {request.method if request.method else ""}')
        if not isinstance(e, RequestEntityTooLarge):
            error_msg_list.append(f'{file_path} Call FORM : {request.form.to_dict() if len(request.form) > 0 else ""}')
        # json 속성은 body에 변환할 데이터가 없는경우 400 Bad Request를 반환함
        # 확인을 위해서는 get_json 함수의 silent=True 를 사용하여 값이 없을경우 None 값을 받도록 해야함
        error_msg_list.append(f'{file_path} Call JSON : {request.get_json(silent=True)}')
    error_msg_list.append(f'{file_path} Exception : {e}')
    error_msg_list.append(f'{file_path} Exception args : {e.args}')
    if msg:
        error_msg_list.append(f'{file_path} Exception msg : {msg}')
    if traceback_str:
        error_msg_list.append(f'{file_path} traceback :\n{traceback_str}')
    error_msg_list.append(f'{file_path} ERROR ========= END')
    # 로거 객체에 따른 출력 분리
    for error_msg in error_msg_list:
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg)


def make_default_error_response(status: HTTPStatus, message):
    """
    기본으로 정의된 에러에 대한 결과 반환
    :param status:
    :type status:
    :param message:
    :type message:
    :return:
    :rtype:
    """
    tmp = datetime.utcnow()
    now = tmp.astimezone(timezone.utc)
    return {
        'timestamp': now.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00"),
        'status': status.value,
        'error': status.phrase,
        'message': message,
        'path': f'{request.path if request.path else ""}'
    }, status.value
