from flask_restx import fields, Model

from ..enums import BoardsCode

# JSON 객체를 위한 Wildcard 모델 설정
# fields.Raw와 같은 여러 Type을 사용할 경우 매핑이 되지 않으니 주의 할것! : java에서의 Map<String, Object>와 같은 형태는 매핑 타입을 알수없어 지원되지 않음
# Wildcard는 key에 대한 패턴 매핑이 가능 : key 패턴에는 그외라는 패턴은 없음
# validate=True 에서 key 패턴에 대한 유효성 검사는 하지 않으므로 패턴이 다른 내용이 저장은 되지만 marshal_with에서 매핑되지 않아 결과에 노출되지 않음
wildcard_multi_model = Model('WildcardMultiModel', {
    '*_str': fields.Wildcard(fields.String(description='추가 정보(문자)')),
    '*_int': fields.Wildcard(fields.Integer(description='추가 정보(숫자)')),
    '*_float': fields.Wildcard(fields.Float(description='추가 정보(숫자:소수점포함)')),
    '*_list_str': fields.Wildcard(fields.List(fields.String, description='추가 목록 정보(문자)'))
    # '*': fields.Wildcard(fields.String(description='추가 정보(default type)'))  # 나머지 설정이 적용되지 않고 무조건 '*' 설정으로 매핑됨
})
# 게시물 상세 Model
board_save_model = Model('BoardSave', {
    'boards_code': fields.String(description='게시물 구분', enum=list([v.name for v in BoardsCode]), attribute='BOARDS_CODE', required=True),
    'title': fields.String(description='게시물 제목', example='제목', attribute='TITLE', required=True, min_length=1, max_length=200),
    'contents': fields.String(description='게시물 내용', example='내용', attribute='CONTENTS', required=True, min_length=1),
    'add_fields': fields.Nested(wildcard_multi_model, description='추가 정보', attribute='ADD_FIELDS', skip_none=True)
})
board_detail_model = board_save_model.inherit('BoardDetail', {
    'board_seq': fields.Integer(description='게시물 번호', example=1, attribute='SEQ'),
    'r_user_id': fields.String(description='작성자', example='UserId', attribute='RUSER'),
    'm_user_id': fields.String(description='수정자', example='UserId', attribute='MUSER'),
    'rdate': fields.DateTime(description='등록일시', example='2023-09-06T14:42:06', attribute='RDATE'),
    'mdate': fields.DateTime(description='수정일시', example='2023-09-06T14:42:06', attribute='MDATE')
})
board_detail_model_for_list = Model('BoardDetailForList', {
    'board_seq': fields.Integer(description='게시물 번호', example=1, attribute='SEQ'),
    'boards_code': fields.String(description='게시물 구분', enum=list([v.name for v in BoardsCode]), attribute='BOARDS_CODE'),
    'title': fields.String(description='게시물 제목', example='제목', attribute='TITLE'),
    'r_user_id': fields.String(description='작성자', example='UserId', attribute='RUSER'),
    'm_user_id': fields.String(description='수정자', example='UserId', attribute='MUSER'),
    'rdate': fields.DateTime(description='등록일시', example='2023-09-06T14:42:06', attribute='RDATE'),
    'mdate': fields.DateTime(description='수정일시', example='2023-09-06T14:42:06', attribute='MDATE')
})
# 게시물 등록 결과
board_save_result_model = Model('BoardSaveResult', {
    'result': fields.String(description='결과', example='Success'),
    'board_seq': fields.Integer(description='게시물 번호', example=1)
})
# 게시물 삭제 결과
board_delete_result_model = Model('BoardDeleteResult', {
    'result': fields.String(description='결과', example='Success'),
    'deleted_count': fields.Integer(description='삭제된 게시물수', example=1)
})
# 게시물 목록 Model
board_list_model = Model('BoardListResult', {
    'totalcount': fields.Integer(description='게시물 전체수', example=100),
    # 게시물 상세 Model을 목록에 사용, skip_none 옵션으로 값이 없는 필드 제거
    'board_list': fields.List(fields.Nested(board_detail_model_for_list, skip_none=True))
})
# 파일 업로드 결과 Model
file_model = Model('File', {
    'file_org_name': fields.String(description='원본 파일명', example='aaa.txt'),
    'file_tmp_path': fields.String(description='파일의 임시 디렉토리', example='tmp'),
    'file_tmp_name': fields.String(description='파일의 임시 파일명', example='beb7728bebcb430c9c63716caed6b808.txt')
})
file_upload_result_model = Model('FileUploadResult', {
    'result': fields.String(description='결과', example='Success'),
    'files': fields.List(fields.Nested(file_model))
})
# 업로드된 파일정보 저장 Model
file_save_model = Model('FileSave', {
    # fields 로 선언되는 모든 타입은 None을 하용하지 않음
    'file_seq': fields.String(description='파일 일련번호', example='번호가 있는 경우 양수(1,2,3), 없는 경우는 공백문자("")'),
    'file_org_name': fields.String(description='원본 파일명', example='aaa.txt', required=True, min_length=1, max_length=255),
    'file_tmp_name': fields.String(description='파일의 임시 파일명', example='beb7728bebcb430c9c63716caed6b808.txt', required=True, min_length=1, max_length=255),
    'file_tmp_path': fields.String(description='파일의 임시 디렉토리', example='tmp', required=True, min_length=1, max_length=255)
})
# 파일정보 상세
file_detail_model = Model('FileDetail', {
    'file_seq': fields.Integer(description='파일 일련번호', example=1, attribute='SEQ'),
    'board_seq': fields.Integer(description='게시물 번호', example=1, attribute='BOARD_SEQ'),
    'file_path': fields.String(description='파일 경로', example='upload', attribute='PATH'),
    'file_name': fields.String(description='파일명', example='beb7728bebcb430c9c63716caed6b808.txt', attribute='FNAME'),
    'file_org_name': fields.String(description='원본 파일명', example='aaa.txt', attribute='ONAME'),
    'rdate': fields.DateTime(description='등록일시', example='2023-09-06T14:42:06', attribute='RDATE'),
    'r_user_id': fields.String(description='작성자', example='UserId', attribute='RUSER')
})
# 실제 파라메터로 넘길 파일정보 목록 Model
file_save_list_model = Model('FileSaveList', {
    'file_list': fields.List(fields.Nested(file_save_model))
})
# 파일 목록 Model
file_list_model = Model('FileList', {
    'board_seq': fields.Integer(description='게시물 번호', example=1),
    'file_list': fields.List(fields.Nested(file_detail_model, skip_none=True))
})
# 파일정보 저장 결과 Model
file_save_result_model = file_list_model.inherit('FileSaveResult', {
    'result': fields.String(description='결과', example='Success')
})
