import os
from time import time
import json

from uuid import UUID
from hashlib import sha256
import hmac
from ssl import SSLContext, PROTOCOL_TLS_SERVER

from collections import OrderedDict
from collections.abc import Callable
from typing import Any

import jwt
from dotenv import load_dotenv
import psycopg
from flask import Flask, Response, jsonify, make_response, redirect, render_template, url_for, request, session

from database import DBHelper, User


HTTP_BAD_REQUEST = 400
HTTP_INTERNAL_SERVER_ERROR = 500


PAGE_MAIN = 'main'

PAGE_BOOKS = 'books'
METHOD_CREATE_BOOK = 'method/create_book'
METHOD_DELETE_BOOK = 'method/delete_book'

PAGE_NOTES = 'notes'
METHOD_CREATE_NOTE = 'method/create_note'
METHOD_DELETE_NOTE = 'method/delete_note'

PAGE_TASK_LISTS = 'task_lists'
METHOD_CREATE_TASK_LIST = 'method/create_task_list'
METHOD_DELETE_TASK_LIST = 'method/delete_task_list'

METHOD_LOGIN = 'method/login'
METHOD_GET_ME = 'method/get_me'


load_dotenv()

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.secret_key = os.environ['APP_KEY']
bot_token = os.environ['BOT_TOKEN']
app.jinja_env.auto_reload = True


ctx = SSLContext(PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(certfile=os.environ['TLS_CERT'], keyfile=os.environ['TLS_KEY'])


database = DBHelper(os.environ['POSTGRES_HOST'], int(os.environ['POSTGRES_PORT']), os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWD'], os.environ['POSTGRES_DBNAME'])


# def template(view_name: str, user: User | None, **kwargs) -> Response:
#     resp = make_response(render_template(f'{view_name}.html', page=view_name, user=user, **kwargs))
#     return resp


# def auth_splitted(f: Callable[[], tuple[Callable[[User], Response], Callable[[], Response]]]) -> Callable[[], Response]:
#     def wrapper() -> Response:
#         user = database.auth(session) # type: ignore
#         return f()[0](user) if user else f()[1]()
#     wrapper.__name__ = f.__name__
#     return wrapper


# def auth_joined(f: Callable[[], Callable[[User | None], Response]]) -> Callable[[], Response]:
#     def wrapper() -> Response:
#         user = database.auth(session) # type: ignore
#         return f()(user)
#     wrapper.__name__ = f.__name__
#     return wrapper


@app.get('/')
def main() -> Response:
    return make_response(render_template(f'{PAGE_MAIN}.html'))


@app.get(f'/{PAGE_BOOKS}')
def books() -> Response:
    return make_response(render_template(f'{PAGE_BOOKS}.html'))


@app.get(f'/{PAGE_NOTES}')
def notes() -> Response:
    return make_response(render_template(f'{PAGE_NOTES}.html'))


@app.get(f'/{PAGE_TASK_LISTS}')
def task_lists() -> Response:
    return make_response(render_template(f'{PAGE_TASK_LISTS}.html'))



def APIError(http_code: int, description: str) -> Response:
    r = make_response(json.dumps(OrderedDict([('ok', False), ('description', description)])), 400)
    r.content_type = 'application/json'
    return r


def APIResult(*result) -> Response:
    r = make_response(json.dumps(OrderedDict([('ok', True), ('result', OrderedDict(result))])))
    r.content_type = 'application/json'
    return r



@app.post(f'/{METHOD_LOGIN}')
def login() -> Response:

    try:
        arguments: dict[Any, Any] = json.loads(request.get_data())
    except:
        return APIError(HTTP_BAD_REQUEST, 'invalid body format')

    try:
        hash = arguments['hash']
        id = int(arguments['id'])
        first_name = arguments['first_name']
        auth_date = int(arguments['auth_date'])
    except:
        return APIError(HTTP_BAD_REQUEST, 'not enough arguments')

    sorted_args = [(k, v) for k, v in sorted(arguments.items(), key=lambda x: x[0]) if k != 'hash']
    data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted_args])
    secret_key = sha256(bot_token.encode()).digest()

    if hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest() != hash:
        return APIError(HTTP_BAD_REQUEST, 'data is not from Telegram')

    timestamp = int(time())
    if timestamp - auth_date > 300:
        return APIError(HTTP_BAD_REQUEST, 'data is outdated')

    database.create_user(id, arguments.get('username', None), first_name, arguments.get('last_name', None))

    auth_token = jwt.encode({'iss': 'https://91.215.155.252:443/', 'sub': id, 'iat': timestamp, 'exp': timestamp+86400}, app.secret_key)
    return APIResult(('auth_token', auth_token))


# @app.post(f'/{METHOD_VALIDATE_TOKEN}')
# def validate_token() -> Response:

#     try:
#         data: dict[Any, Any] = request.json # type: ignore
#     except:
#         return jsonify(OrderedDict([('ok', False), ('description', 'body is not a json')]))

#     if not (encoded_token := str(data.get('auth_token', ''))):
#         return jsonify(OrderedDict([('ok', False), ('description', 'not enough arguments')]))

#     decoded_token: dict[Any, Any] = jwt.decode(encoded_token, app.secret_key, algorithms=[jwt.get_unverified_header(encoded_token)['alg']])

#     if int(time()) > decoded_token['exp']:
#         return jsonify(OrderedDict([('ok', False), ('description', 'token expired')]))

#     return jsonify(OrderedDict([('ok', True), ('result', decoded_token)]))

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


# @app.get(f'/{PAGE_BOOKS}')
# @auth_splitted
# def books() -> tuple[Callable[[User], Response], Callable[[], Response]]:

#     def ok(user: User) -> Response:
#         books = database.get_books(user.id)
#         return template(PAGE_BOOKS, user, books=books)

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.post(f'/{METHOD_CREATE_BOOK}')
# @auth_splitted
# def create_book() -> tuple[Callable[[User], Response], Callable[[], Response]]:

#     def ok(user: User) -> Response:
#         if not (title := request.form.get('title', None)):
#             return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
#         if not database.create_book(user.id, title):
#             return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
#         return redirect(url_for(books.__name__)) # type: ignore

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.post(f'/{METHOD_DELETE_BOOK}')
# @auth_splitted
# def delete_book():

#     def ok(user: User) -> Response:
#         if not (book_id := request.form.get('book_id')):
#             return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
#         if not database.delete_book(user.id, UUID(book_id)):
#             return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
#         return redirect(url_for(books.__name__)) # type: ignore

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.get(f'/{PAGE_NOTES}')
# @auth_splitted
# def notes():

#     def ok(user: User) -> Response:
#         return template(PAGE_NOTES, user, book_id=request.args['book_id'], notes=database.get_notes(user.id, UUID(request.args['book_id'])))

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.post(f'/{METHOD_CREATE_NOTE}')
# @auth_splitted
# def create_note():

#     def ok(user: User) -> Response:
#         if not all((book_id := request.form['book_id'], title := request.form['title'], text := request.form['text'])):
#             return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
#         if not database.create_note(user.id, UUID(book_id), title, text):
#             return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
#         return redirect(url_for(notes.__name__, book_id=book_id)) # type: ignore

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.post(f'/{METHOD_DELETE_NOTE}')
# @auth_splitted
# def delete_note():

#     def ok(user: User) -> Response:
#         return redirect(url_for(main.__name__)) # type: ignore

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.get(f'/{PAGE_TASK_LISTS}')
# @auth_splitted
# def task_lists():

#     def ok(user: User) -> Response:
#         return template(PAGE_TASK_LISTS, user, tasklists=database.get_tasklists(user.id))

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.post(f'/{METHOD_CREATE_TASK_LIST}')
# @auth_splitted
# def create_task_list():

#     def ok(user: User) -> Response:
#         if not all((title := request.form.get('title', None), tasks := request.form.getlist('task'))):
#             return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
#         if not database.create_tasklist(user.id, title, tasks): # type: ignore
#             return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
#         return redirect(url_for(task_lists.__name__)) # type: ignore

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


app.run(os.environ['LISTEN_ADDR'], int(os.environ['LISTEN_PORT']), ssl_context=ctx)
