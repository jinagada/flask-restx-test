# 전역상수가 필요한 경우 가급적 별도 상수 파일에 작성하여 모든 파일에서 사용가능하게 할것!!
# 프로젝트 ID
PROJECT_ID = 'flask-restx-test'
# 파일경로
PathConfig = {
    'local': {
        'file_upload_home': f'__FULL_PATH__/{PROJECT_ID}/static',
        'file_tmp_path': 'tmp',
        'file_path': 'upload'
    },
    'dev': {
        'file_upload_home': f'__FULL_PATH__/{PROJECT_ID}/static',
        'file_tmp_path': 'tmp',
        'file_path': 'upload'
    }
}
