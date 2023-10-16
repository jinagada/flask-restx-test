from flask_restx import reqparse


# 목록 조회 query 공통 파라메터
# type=int 인 경우 파라메터에 값이 없으면, default 값이 있어도 parse_args 실행시 설정이 되지 않음
common_list_params = reqparse.RequestParser()
common_list_params.add_argument('start_row', location='args', type=int, required=True, default=0, help='시작행 번호')
common_list_params.add_argument('row_per_page', location='args', type=int, required=True, default=10, help='화면당 행 수')
