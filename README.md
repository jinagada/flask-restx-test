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
* flask-jwt-extended 4.5.2
* flask-babel 3.1.0

# 참고 문서
- [Welcome to Flask-RESTX’s documentation!](https://flask-restx.readthedocs.io/en/latest/index.html)
  - path에 문서 적용 예제
  ```python
  @api.route('/check/<enum_list:values>')
  @api.param('values', 'description', enum=list([v.name for v in Enums]), example='예제')
  ```
  - Java에서 Map<String, String>으로된 스키마의 표현 방법
  ```python
  'data': fields.Wildcard(fields.String(description='설명'), description='설명')
  ```
  ```text
  data {
    description: 설명
    < * >: string
           설명
  }
  ```
- [Flask-JWT-Extended’s Documentation](https://flask-jwt-extended.readthedocs.io/en/stable/)
- [Flask-Babel](https://python-babel.github.io/flask-babel/)
- [Welcome to Flask(English)](https://flask-docs.readthedocs.io/en/latest/)
- [Welcome to Flask(Korean)](https://flask-docs-kr.readthedocs.io/ko/latest/)
  - [URL Converters](https://exploreflask.com/en/latest/views.html#custom-converters)
    - 예제 1
    ```python
    from werkzeug.routing import BaseConverter
  
    class IntListConverter(BaseConverter):
        regex = r'\d+(?:,\d+)*,?'
  
        def to_python(self, value):
            return [int(x) for x in value.split(',')]
  
        def to_url(self, value):
            return ','.join(str(x) for x in value)
    ```
    ```python
    app = Flask(__name__)
    app.url_map.converters['int_list'] = IntListConverter
    ```
    ```python
    @app.route('/add/<int_list:values>')
    @app.param('values', '설명', example='1,2,3')
    def add(values):
        return str(sum(values))
    ```
    - 예제 2
    ```python
    from flask import Flask
    from enum import Enum, unique
    from werkzeug.routing import BaseConverter, ValidationError
  
    @unique
    class RequestType(str, Enum):
        TYPE1 = 'abc'
        TYPE2 = 'def'
  
    class RequestTypeConverter(BaseConverter):
  
        def to_python(self, value):
            try:
                request_type = RequestType(value)
                return request_type
            except ValueError as err:
                raise ValidationError()
  
        def to_url(self, obj):
            return obj.value
  
  
    app = Flask(__name__)
    app.url_map.converters.update(request_type=RequestTypeConverter)
  
    @app.route('/api/v1/<request_type:t>', methods=['POST'])
    def root(t):
        return f'{t.name} -> {t.value}'
    ```

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

## Flask-Babel
### 기본 locale 설정

```python
# Flask 생성
app = Flask(__name__)
# Babel 생성
babel = Babel(app)
# Babel locale 기본값을 한국어(ko)로 설정
app.config['BABEL_DEFAULT_LOCALE'] = 'ko'
```

### 작업순서

1. 소스에 각 메시지 작성
   * 기본 locale 로 설정한 언어로 메시지를 작성 할 것

```python
raise NotFound(gettext(u'게시물이 존재하지 않습니다.'))
```

2. babel.cfg 파일 생성

```text
[python: **.py]
[jinja2: **/templates/**.html]
extensions=jinja2.ext.autoescape,jinja2.ext.with_
```

3. .pot 파일 생성

```bash
$ cd app
$ pybabel extract -F babel.cfg -o messages.pot .
```

4. 언어별 디렉토리 및 언어별 .po 파일 생성
   * 기본 locale 을 설정한 경우 해당 메시지는 gettext에 작성된 메시지로 보여짐

```bash
$ pybabel init -i messages.pot -d ./translations -l en
$ pybabel init -i messages.pot -d ./translations -l ja
$ pybabel init -i messages.pot -d ./translations -l zh
```

5. .po 파일에 번역 작성하기

```text
#: apis/BoardSample.py:184 apis/BoardSample.py:220 apis/BoardSample.py:280
#: apis/BoardSample.py:300 services/BoardService.py:99
msgid "게시물이 존재하지 않습니다."
msgstr "This post does not exist."
```

6. 컴파일 하기 : .mo 파일 생성

```bash
$ pybabel compile -f -d ./translations
```

### 소스의 변경사항 처리
1. .pot 파일 재생성

```bash
$ cd app
$ pybabel extract -F babel.cfg -o messages.pot .
```

2. .po 파일 갱신처리

```bash
$ pybabel update -i messages.pot -d ./translations
```

3. 컴파일 하기

```bash
$ pybabel compile -f -d ./translations
```
