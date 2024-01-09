import os
from time import time

from uuid import UUID
from hashlib import sha256
import hmac
from ssl import SSLContext, PROTOCOL_TLS_SERVER

from collections import OrderedDict
from collections.abc import Callable
from typing import Any

import jwt
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, make_response, redirect, render_template, url_for, request, session

from database import DBHelper, User


PAGE_ERROR = 'error'

PAGE_MAIN = 'main'

PAGE_BOOKS = 'books'
METHOD_CREATE_BOOK = 'method/create-book'
METHOD_DELETE_BOOK = 'method/delete-book'

PAGE_NOTES = 'notes'
METHOD_CREATE_NOTE = 'method/create-note'
METHOD_DELETE_NOTE = 'method/delete-note'

PAGE_TASK_LISTS = 'task-lists'
METHOD_CREATE_TASK_LIST = 'method/create-task-list'
METHOD_DELETE_TASK_LIST = 'method/delete-task-list'

METHOD_LOGIN = 'method/login'
METHOD_LOGOUT = 'method/logout'


# API_GET_BOOKS = 'get_books'
# API_CREATE_BOOK = 'create_book'
# API_DELETE_BOOK = 'delete_book'

# API_GET_NOTES = 'get_notes'
# API_CREATE_NOTE = 'create_note'
# API_DELETE_NOTE = 'delete_note'

# API_GET_TASK_LISTS = 'get_task_lists'
# API_CREATE_TASK_LIST = 'create_task_list'
# API_DELETE_TASK_LIST = 'delete_task_list'


load_dotenv()

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.secret_key = os.environ['APP_KEY']
bot_token = os.environ['BOT_TOKEN']
app.jinja_env.auto_reload = True


ctx = SSLContext(PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(certfile=os.environ['TLS_CERT'], keyfile=os.environ['TLS_KEY'])


database = DBHelper(os.environ['POSTGRES_HOST'], int(os.environ['POSTGRES_PORT']), os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWD'], os.environ['POSTGRES_DBNAME'])


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
        return template(PAGE_MAIN, None, total_notes_count=0)

    return ok, err


@app.get('/error')
@auth_joined
def error() -> Callable[[User | None], Response]:

    def page(user: User | None) -> Response:
        return template(PAGE_ERROR, user, msg=request.args.get('msg', 'Неизвестная ошибка'))

    return page


@app.post(f'/{METHOD_LOGIN}')
def login() -> Response:

    try:
        data: dict[Any, Any] = request.json # type: ignore
    except:
        return jsonify(OrderedDict([('ok', False), ('description', 'body is not a json')]))

    if not all([hash := str(data.get('hash', '')), id := int(data.get('id', 0)), first_name := str(data.get('first_name', '')), auth_date := int(data.get('auth_date', 0))]):
        return jsonify(OrderedDict([('ok', False), ('description', 'not enough arguments')]))

    sorted_args = [(k, v) for k, v in sorted(data.items(), key=lambda x: x[0]) if k != 'hash']
    data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted_args])
    secret_key = sha256(bot_token.encode()).digest()

    if hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest() != hash:
        return jsonify(OrderedDict([('ok', False), ('description', 'data is not from Telegram')]))

    timestamp = int(time())
    if timestamp - auth_date > 300:
        return jsonify(OrderedDict([('ok', False), ('description', 'data is outdated')]))

    auth_token = jwt.encode({'iss': 'https://91.215.155.252:443/', 'sub': id, 'exp': timestamp+86400, 'iat': timestamp}, app.secret_key)
    return jsonify(OrderedDict([('ok', True), ('result', OrderedDict([('auth_token', auth_token)]))]))


# @app.get(f'/{METHOD_LOGIN}')
# def login() -> Response:

#     if not (tg_hash := request.args.get('hash')):
#         return redirect(url_for(error.__name__, msg='Параметр `hash` отсутствует в ответе от Telegram')) # type: ignore

#     sorted_args = [(k, v) for k, v in sorted(request.args.items(), key=lambda x: x[0]) if k != 'hash']

#     data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted_args])
#     secret_key = hashlib.sha256(bot_token.encode()).digest()

#     if hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest() != tg_hash:
#         return redirect(url_for(error.__name__, msg='Нарушена целостность данных, полученных от Telegram')) # type: ignore

#     for k, v in sorted_args:
#         session[k] = v

#     return redirect(url_for(main.__name__)) # type: ignore


@app.get(f'/{PAGE_BOOKS}')
@auth_splitted
def books() -> tuple[Callable[[User], Response], Callable[[], Response]]:

    def ok(user: User) -> Response:
        books = database.get_books(user.id)
        return template(PAGE_BOOKS, user, books=books)

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
        if not database.delete_book(user.id, UUID(book_id)):
            return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
        return redirect(url_for(books.__name__)) # type: ignore

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err


@app.get(f'/{PAGE_NOTES}')
@auth_splitted
def notes():

    def ok(user: User) -> Response:
        return template(PAGE_NOTES, user, book_id=request.args['book_id'], notes=database.get_notes(user.id, UUID(request.args['book_id'])))

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err


@app.post(f'/{METHOD_CREATE_NOTE}')
@auth_splitted
def create_note():

    def ok(user: User) -> Response:
        if not all((book_id := request.form['book_id'], title := request.form['title'], text := request.form['text'])):
            return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
        if not database.create_note(user.id, UUID(book_id), title, text):
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
        return template(PAGE_TASK_LISTS, user, tasklists=database.get_tasklists(user.id))

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err


@app.post(f'/{METHOD_CREATE_TASK_LIST}')
@auth_splitted
def create_task_list():

    def ok(user: User) -> Response:
        if not all((title := request.form.get('title', None), tasks := request.form.getlist('task'))):
            return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
        if not database.create_tasklist(user.id, title, tasks): # type: ignore
            return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
        return redirect(url_for(task_lists.__name__)) # type: ignore

    def err() -> Response:
        return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

    return ok, err


app.run(os.environ['LISTEN_ADDR'], int(os.environ['LISTEN_PORT']), ssl_context=ctx)
