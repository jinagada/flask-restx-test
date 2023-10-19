from flask_restx import reqparse


# 목록 조회 query 공통 파라메터
# type=int 인 경우 파라메터에 값이 없으면, default 값이 있어도 parse_args 실행시 설정이 되지 않음
# enum 객체는 choices=tuple([]) 을 사용하여 등록
# type에는 type=inputs.email() 와 같은 객체를 사용가능
# reqparse.Argument()를 사용하여 argument 객체를 생성후 재사용 할 수 있음
# replace_argument()을 사용하여 이미 설정된 attr 값을 변경 할 수 있음. 설정한 파라메터를 모두 작성 해 주어야함
# 예) params.add_argument(argument_obj).replace_argument(argument_obj.name, location=argument_obj.location, type=argument_obj.type, required=argument_obj.required, help='수정된 설명')
common_list_params = reqparse.RequestParser()
common_list_params.add_argument('start_row', location='args', type=int, required=True, default=0, help='시작행 번호')
common_list_params.add_argument('row_per_page', location='args', type=int, required=True, default=10, help='화면당 행 수')
