from app import app, init_app


init_app('local')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
