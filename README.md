# 샘플 프로젝트 정보
이미 설치된 프로그램들
* conda version : 23.7.3
* Python 3.7.12
* Flask 2.1.3
* Flask-Bootstrap 3.3.7.1
* Jinja2 3.1.2
* Werkzeug 2.2.3
* flask-restx 1.0.6
* Sqlite 3.43.0

# 참고 문서
- [Welcome to Flask-RESTX’s documentation!](https://flask-restx.readthedocs.io/en/latest/index.html)
- [Flask-JWT-Extended’s Documentation](https://flask-jwt-extended.readthedocs.io/en/stable/)
- [Welcome to Flask(English)](https://flask-docs.readthedocs.io/en/latest/)
- [Welcome to Flask(Korean)](https://flask-docs-kr.readthedocs.io/ko/latest/)

## PyCharm 에서 Flask 프로젝트 생성
### 개발서버 디렉토리 생성
* sample-test env 사용

```bash
$ mkdir ~/anaconda3/envs/sample-test/project/flask-restx-test
```

### PyCharm에서 생성한 디릭토리와 연동하여 Flask 프로젝트 생성
* PyCharm 과 연동하는 부분의 설명은 생략
* Run/Debug Configuration에서 Flask Server 로 실행하는 경우 Additional options에 아래의 내용을 추가

```text
--host=0.0.0.0 --port=5000
```

### PyCharm에서 생성된 프로젝트에서 Flask 개발모드 실행
* 실행결과

```bash
 * Serving Flask app 'app' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.87.44:5000
```

## 개발모드에서 사용되는 5000 포트 개발서버 방화벽 설정

```bash
$ sudo firewall-cmd --permanent --add-port=5000/tcp
$ sudo firewall-cmd --reload
$ sudo systemctl restart firewalld
```

## logrotate 설정
* LOG BASE : ~/logs/flask-restx-test

```bash
$ sudo vi /etc/logrotate.d/flask-restx-test
```

* 내용

```bash
{LOG BASE}/*.log {
    copytruncate
    daily
    rotate 15
    maxage 7
    missingok
    notifempty
    compress
    dateext
    dateformat -%Y%m%d_%s
    postrotate
        /bin/chown {USERID}:{USERGROUP} {LOG BASE}/*.log*
    endscript
    su root {USERGROUP}
}
```

## 소스에 설정된 ApiDoc URL
* URL : http://localhost:5000/api/v1/docs
