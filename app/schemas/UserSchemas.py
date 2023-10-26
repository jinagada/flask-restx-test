from flask_restx import fields, Model

from ..enums import AuthCode

# 로그인 Model
login_model = Model('Login', {
    'user_id': fields.String(description='사용자ID', example='UserId', required=True, min_length=5),
    'password': fields.String(description='비밀번호', example='12#$qw', required=True, min_length=5),
})
jwt_token_login_model = Model('JWTTokenLogin', {
    'access_token': fields.String(description='JWT Access Token', example='JWT TOKEN'),
    'refresh_token': fields.String(description='JWT Refresh Token', example='JWT TOKEN')
})
jwt_token_refresh_model = Model('JWTTokenRefresh', {
    'access_token': fields.String(description='JWT Access Token', example='JWT TOKEN')
})
# 사용자 상세 Model
user_save_model = Model('UserSave', {
    'user_id': fields.String(description='사용자ID', example='UserId', attribute='USER_ID', required=True, min_length=5, max_length=20),
    'password': fields.String(description='비밀번호', example='Password', attribute='USER_PW', required=True, min_length=5, max_length=15),
    'user_name': fields.String(description='사용자명', example='UserName', attribute='USER_NAME', required=True, min_length=2, max_length=50),
    'auth_code': fields.String(description='권한코드', example='USER', attribute='AUTH_CODE', required=True, enum=list([v.name for v in AuthCode]))
})
user_detail_model = user_save_model.inherit('UserDetail', {
    'user_seq': fields.Integer(description='사용자 번호', example=1, attribute='SEQ'),
    'rdate': fields.DateTime(description='등록일시', example='2023-09-06T14:42:06', attribute='RDATE'),
    'mdate': fields.DateTime(description='수정일시', example='2023-09-06T14:42:06', attribute='MDATE')
})
# 사용자 등록 결과
user_save_result_model = Model('UserSaveResult', {
    'result': fields.String(description='결과', example='Success'),
    'user_seq': fields.Integer(description='사용자 번호', example=1)
})
# 사용자 삭제 결과
user_delete_result_model = Model('UserDeleteResult', {
    'result': fields.String(description='결과', example='Success'),
    'deleted_count': fields.Integer(description='삭제된 사용자수', example=1)
})
# 사용자 목록 Model
# fields.Nested의 경우 파라메터로 Model 객체가 필요함
user_list_model = Model('UserListResult', {
    'totalcount': fields.Integer(description='사용자 전체 수', example=100),
    'user_list': fields.List(fields.Nested(user_detail_model, skip_none=True))
})
# current_user 및 권한 Model
jwt_login_info_model = Model('JWTLoginInfo', {
    'current_user': fields.Nested(user_detail_model, skip_none=True),
    'claims': fields.Raw(description='JWT TOKEN 상세내용', example='dict 형식의 상세내용')
})
