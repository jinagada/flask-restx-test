from flask_restx import fields, Model


# 기본 오류 메시지
default_error_model = Model('DefaultErrorMsg', {
    'timestamp': fields.DateTime(description='오류발생 시간', example='2023-10-12T21:34:34.617561+00:00'),
    'status': fields.Integer(description='Http Status 코드', example='403'),
    'error': fields.String(description='Http Status 코드명', example='Forbidden'),
    'message': fields.String(description='오류 메시지', example='오류 메시지'),
    'path': fields.String(description='URL Path', example='')
})
