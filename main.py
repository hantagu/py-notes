import os
import hmac
import hashlib
from collections.abc import Callable

from ssl import SSLContext, PROTOCOL_TLS_SERVER

from flask import Flask, Response, make_response, redirect, render_template, url_for, request, session

from database import DBHelper, User


PAGE_ERROR = 'error'

PAGE_MAIN = 'main'

PAGE_BOOKS = 'books'
METHOD_CREATE_BOOK = 'create-book'
METHOD_DELETE_BOOK = 'delete-book'

PAGE_NOTES = 'notes'
METHOD_CREATE_NOTE = 'create-note'
METHOD_DELETE_NOTE = 'delete-note'

PAGE_TASK_LISTS = 'task-lists'
METHOD_CREATE_TASK_LIST = 'create-task-list'
METHOD_DELETE_TASK_LIST = 'delete-task-list'

METHOD_LOGIN = 'login'
METHOD_LOGOUT = 'logout'


app = Flask(__name__)
app.secret_key = os.environ['APP_KEY']
bot_token = os.environ['BOT_TOKEN']
app.jinja_env.keep_trailing_newline = True


ctx = SSLContext(PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(certfile=f'./tls/{os.environ["LISTEN_ADDR"]}.crt', keyfile=f'./tls/{os.environ["LISTEN_ADDR"]}.key')


database = DBHelper(os.environ['MYSQL_HOST'], os.environ['MYSQL_USER'], os.environ['MYSQL_PASSWD'], os.environ['MYSQL_DATABASE'])


def template(view_name: str, user: User | None, **kwargs) -> Response:
    resp = make_response(render_template(f'{view_name}.html', page=view_name, user=user, **kwargs))
    return resp


def auth_splitted(f: Callable[[], tuple[Callable[[User], Response], Callable[[], Response]]]) -> Callable[[], Response]:
    def wrapper() -> Response:
        user = database.auth(session) # type: ignore
        return f()[0](user) if user else f()[1]()
    wrapper.__name__ = f.__name__
    return wrapper


def auth_joined(f: Callable[[], Callable[[User | None], Response]]) -> Callable[[], Response]:
    def wrapper() -> Response:
        user = database.auth(session) # type: ignore
        return f()(user)
    wrapper.__name__ = f.__name__
    return wrapper


@app.get('/')
@auth_splitted
def main() -> tuple[Callable[[User], Response], Callable[[], Response]]:

    def ok(user: User) -> Response:
        return template(PAGE_MAIN, user)

    def err() -> Response:
        return template(PAGE_MAIN, None, total_notes_count=database.total_notes_count())

    return ok, err


@app.get('/error')
@auth_joined
def error() -> Callable[[User | None], Response]:

    def page(user: User | None) -> Response:
        return template(PAGE_ERROR, user, msg=request.args.get('msg', 'Неизвестная ошибка'))

    return page


@app.get(f'/{METHOD_LOGIN}')
def login() -> Response:

    if not (tg_hash := request.args.get('hash')):
        return redirect(url_for(error.__name__, msg='Параметр `hash` отсутствует в ответе от Telegram')) # type: ignore

    sorted_args = [(k, v) for k, v in sorted(request.args.items(), key=lambda x: x[0]) if k != 'hash']

    data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted_args])
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    if hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest() != tg_hash:
        return redirect(url_for(error.__name__, msg='Нарушена целостность данных, полученных от Telegram')) # type: ignore

    for k, v in sorted_args:
        session[k] = v

    return redirect(url_for(main.__name__)) # type: ignore


@app.get(f'/{METHOD_LOGOUT}')
def logout() -> Response:
    session.clear()
    return redirect(url_for(main.__name__)) # type: ignore


@app.get(f'/{PAGE_BOOKS}')
@auth_splitted
def books() -> tuple[Callable[[User], Response], Callable[[], Response]]:

    def ok(user: User) -> Response:
        return template(PAGE_BOOKS, user, books=database.get_books(user.id))

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err


@app.post(f'/{METHOD_CREATE_BOOK}')
@auth_splitted
def create_book() -> tuple[Callable[[User], Response], Callable[[], Response]]:

    def ok(user: User) -> Response:
        if not (title := request.form.get('title', None)):
            return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
        if not database.create_book(user.id, title):
            return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
        return redirect(url_for(books.__name__)) # type: ignore

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err


@app.post(f'/{METHOD_DELETE_BOOK}')
@auth_splitted
def delete_book():

    def ok(user: User) -> Response:
        if not (book_id := request.form.get('book_id')):
            return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
        if not database.delete_book(user.id, int(book_id)):
            return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
        return redirect(url_for(books.__name__)) # type: ignore

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err


@app.get(f'/{PAGE_NOTES}')
@auth_splitted
def notes():

    def ok(user: User) -> Response:
        return template(PAGE_NOTES, user, book_id=request.args['book_id'], notes=database.get_notes(user.id, int(request.args['book_id'])))

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err


@app.post(f'/{METHOD_CREATE_NOTE}')
@auth_splitted
def create_note():

    def ok(user: User) -> Response:
        if not all((book_id := request.form['book_id'], title := request.form['title'], text := request.form['text'])):
            return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
        if not database.create_note(user.id, int(book_id), title, text):
            return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
        return redirect(url_for(notes.__name__, book_id=book_id)) # type: ignore

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err


@app.post(f'/{METHOD_DELETE_NOTE}')
@auth_splitted
def delete_note():

    def ok(user: User) -> Response:
        return redirect(url_for(main.__name__)) # type: ignore

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err


@app.get(f'/{PAGE_TASK_LISTS}')
@auth_splitted
def task_lists():

    def ok(user: User) -> Response:
        return template(PAGE_TASK_LISTS, user)

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err

app.run(os.environ['LISTEN_ADDR'], 443, ssl_context=ctx)
